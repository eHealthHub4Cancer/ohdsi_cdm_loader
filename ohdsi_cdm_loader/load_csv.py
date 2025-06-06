import os
import pandas as pd
import rpy2.robjects as robjs
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError
from .db_connector import DatabaseHandler
import logging
import time
import asyncio
import pyarrow.feather as feather
from pg_bulk_loader import PgConnectionDetail, batch_insert_to_postgres
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set the event loop policy to WindowsSelectorEventLoopPolicy if using Windows
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class CSVLoader:
    def __init__(self, conn=None, db_handler=None, 
                 # Alias parameters to match documentation
                 db_connection=None, database_handler=None):
        """
        Initialize the CSVLoader class.

        Args:
            conn (object): Database connection object.
            db_handler (object): Database handler object.
            
            # Documentation aliases
            db_connection (object): Alias for conn - Database connection object.
            database_handler (object): Alias for db_handler - Database handler object.
        """
        # Handle the alias parameters
        conn = db_connection if conn is None else conn
        db_handler = database_handler if db_handler is None else db_handler
        
        # Check for required parameters
        if conn is None or db_handler is None:
            missing = []
            if conn is None: missing.append("conn/db_connection")
            if db_handler is None: missing.append("db_handler/database_handler")
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        
        self.conn = conn
        self.schema = db_handler._schema
        self.db_connect = db_handler
        self.db_con = importr('DatabaseConnector')
        self.db_connector = self.db_connect.get_db_connector()
        self._arrow = importr('arrow')
        self._bulk_conn = db_handler.get_bulk_connection()
        self._character = {}
        
    def r2p_convert(self, rdf: object, direction: str) -> object:
        """
        Compare the data frame columns with the database schema and convert columns as necessary.

        Args:
            rdf (object): R data frame to be compared and converted.
            schema_dict (dict): Dictionary containing column names and expected data types.

        Returns:
            object: The modified R data frame with converted data types.
        """
        if direction == 'to_python':
             self._arrow.write_feather(rdf, 'temp.feather')
             rdf = feather.read_feather('temp.feather')
        elif direction == 'to_r':
            feather.write_feather(rdf, 'temp.feather')
            rdf = self._arrow.read_feather('temp.feather')
        return rdf

    def check_data_types(self, rdf: object, result_schema, similar_columns) -> None:
        """
        Check the data types of the columns in the data frame and convert them as necessary.
        """
        similar_columns = list(similar_columns)
        # Select only the similar columns from the R data frame
        new_rdf = rdf[similar_columns].copy()

        # Iterate through each column to convert based on the database schema
        for column in similar_columns:
            if result_schema[column] in ['integer', 'bigint', 'smallint']:
                new_rdf[column] = pd.to_numeric(new_rdf[column], errors='coerce').astype('Int64')
            if result_schema[column] in ['numeric']:
                new_rdf[column] = pd.to_numeric(new_rdf[column], errors='coerce')
            if result_schema[column] in ['character','character varying']:
                new_rdf[column] = new_rdf[column].fillna('').astype(str)
                new_rdf[column] = new_rdf[column].str[:int(self._character[column])]
            elif result_schema[column] in ['date', 'Date']:
                new_rdf[column] = pd.to_datetime(new_rdf[column], format='%Y%m%d', errors='coerce')
            elif result_schema[column] == 'logical':
                new_rdf[column] = new_rdf[column].astype(bool)
            elif result_schema[column] == 'complex':
                new_rdf[column] = new_rdf[column].astype(complex)
        return new_rdf
    
    def compare_and_convert(self, rdf: object, table: str):
        """
        Compare the data frame columns with the database schema and convert columns as necessary
        rdf: R data frame to be compared and converted.
        table: table name to compare the schema with
        """
        # get the data type for the table, including the columns
        query = f"SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = '{table}' and table_schema = '{self.schema}'"
        result = self.db_con.querySql(
            connection=self.conn,
            sql=query)
        
        result = self.r2p_convert(result, 'to_python')
        # create a dictionary of the columns and their data types
        result_schema = dict(zip(result['COLUMN_NAME'], result['DATA_TYPE']))
        self._character = dict(zip(result['COLUMN_NAME'], result['CHARACTER_MAXIMUM_LENGTH']))
        # drop all rows without value.
        rdf = rdf.dropna(axis=1, how='all')
        required_columns = set(result_schema.keys())
        dataframe_columns = set(rdf.columns)
        # similar_columns 
        similar_columns = required_columns.intersection(dataframe_columns)

        return self.check_data_types(rdf, result_schema, similar_columns)
    
    async def bulk_load_data(self, batch_size, data, table_name, max_pool_size: int=20, min_pool_size:int=20):
        """ bulk load data into database
        Args:
            batch_size: int representing batches
            data: pandas dataframe represent the dataframe data to be loaded.
            table_name: string representing the table name.
            max_pool_size: int
            min_pool_size: int
        """    
        # Calculate the total number of batches using the provided batch size
        num_batches = (len(data) + batch_size - 1) // batch_size

        # Insert data into the database in batches with progress tracking
        for i in tqdm(range(num_batches), desc="Inserting batches into database"):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(data))
            batch_data = data.iloc[start_idx:end_idx]

            # Insert each batch into the database
            await batch_insert_to_postgres(
                pg_conn_details=self._bulk_conn,
                table_name=table_name,
                input_data=batch_data,
                batch_size=batch_size,
                min_conn_pool_size=min_pool_size,
                max_conn_pool_size=max_pool_size,
                use_multi_process_for_create_index=False,
                drop_and_create_index=False
            )

    async def load_csv_to_db(self, file_path: str, table_name: str, chunk_size:int=100000, batch_size: int= 500000, synthea: bool=False) -> None:
        """
        Load a CSV file into the specified database table.

        Args:
            file_path (str): Path to the CSV file.
            table_name (str): Name of the database table.

        Returns:
            None
        """
        try:
            if synthea:
                chunks = pd.read_csv(file_path, chunksize=chunk_size, low_memory=False)
            else:
                chunks = pd.read_csv(file_path, sep='\t', na_values=[], keep_default_na=False, chunksize=chunk_size, low_memory=False)
            # list to hold chunk while loading.
            df_list = []
            for chunk in tqdm(chunks, desc="Reading CSV in chunks"):
                df_list.append(chunk)

            # concatenate chunks.    
            df = pd.concat(df_list, ignore_index=True)
            rdf_2 = df.copy(deep=True)
            rdf_2.columns = rdf_2.columns.str.lower()
            # # Convert data types
            cleaned_rdf = self.compare_and_convert(rdf_2, table_name)
            await self.bulk_load_data(batch_size=batch_size,
                                data=cleaned_rdf,
                                table_name=table_name,
                                max_pool_size=20,
                                min_pool_size=20)
      
            logging.info(f"Loaded data into table '{self.schema}.{table_name}'.")

        except Exception as e:
            raise RuntimeError(f"Error loading '{file_path}' into '{table_name}': {e}")

    def load_all_csvs(self, folder_path: str, table_order: list=['vocabulary', 
            'domain', 'concept_class', 'concept', 'relationship', 'concept_relationship', 
            'concept_ancestor', 'concept_synonym', 'drug_strength'], upper: bool=True, synthea: bool=False) -> None:
        """
        Load all CSV files from the specified folder into the database schema.

        Args:
            folder_path (str): Path to the folder containing CSV files.

        Returns:
            None
        """
        table_order = table_order
        file_to_table_mapping = {f"{table}.csv": table.lower() for table in table_order}
        missing_files = []

        try:
            print("\n\nDeleting data from table before loading...\n\n")
            time.sleep(1)
            a = [self.db_connect.empty_table(self.schema, table_name) for table_name in table_order]
            time.sleep(1)
            print("\n\n Next - Inserting data...\n\n")
            time.sleep(1)
        except Exception as e:
            logging.error(f"Failed to empty table': {e}")


        for table in table_order:
            filename = file_to_table_mapping.get(f'{table}.csv')
            print(filename)
            if filename:
                table_name = table.upper() if upper else table
                self.db_connect.disable_foreign_key_checks(table_name)
                print(f"Table: {table_name}") if upper else None
                file_path = os.path.join(folder_path, f'{table_name}.csv')
                if os.path.exists(file_path):
                    try:
                        asyncio.run(self.load_csv_to_db(file_path, table_name, synthea=synthea))
                    except Exception as e:
                        raise RuntimeError(f"Failed to load '{filename}' into '{table_name}': {e}")
                else:
                    logging.warning(f"File '{filename}' not found in folder '{folder_path}'.")
                    missing_files.append(filename)
        
        self.db_connect.enable_foreign_key_checks()

        if missing_files:
            logging.warning(f"Missing files: {missing_files}")

        logging.info("All CSV files have been processed.")