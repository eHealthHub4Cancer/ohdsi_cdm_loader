import os
import pandas as pd
import rpy2.robjects as robjs
from rpy2.robjects.packages import importr
from rpy2.robjects import default_converter
from rpy2.robjects.conversion import localconverter
from rpy2.rinterface_lib.embedded import RRuntimeError


import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import R packages
try:
    db_connector = importr('DatabaseConnector')
    readr = importr('readr')
    base = importr('base')
    lubridate = importr('lubridate')  # For date handling
    ymd = lubridate.ymd
    dplyr = importr('dplyr')

except RRuntimeError as e:
    raise Exception(f"Failed to import R package 'DatabaseConnector': {e}")

def get_table_schema(conn, schema, table_name):
    """
    Retrieves the column names and data types from the target PostgreSQL table.
    
    Args:
        conn: Database connection object.
        schema: Database schema name.
        table_name: Name of the table to retrieve the schema from.

    Returns:
        dict: A dictionary of column names and their corresponding data types.
    """

    query = f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = '{table_name}';
    """
    # run the query.
    result = db_connector.querySql(conn, query)
    data = {}
    # Loop through each column in the R DataFrame dynamically
    colnames = robjs.r.colnames(result)

    for col_name in colnames:
        column_data = list(result.rx2(col_name))  # Extract the column data as a list
        data[col_name] = column_data  # Add the column to the dictionary
    
    # zip this to contain both key and value, where key is the column name and value is the data_type returned.
    schema_dict = dict(zip(data['COLUMN_NAME'], data['DATA_TYPE']))

    return schema_dict

def compare_and_convert_data_types(rdf, schema_dict):
    """
    Compares the data frame columns with the PostgreSQL schema and converts columns as necessary.
    
    Args:
        rdf: The loaded R data frame from the CSV.
        schema_dict: Dictionary of column names and data types from PostgreSQL.
    
    Returns:
        rdf: The modified R data frame with converted data types.
    """
    col_names = base.colnames(rdf)  # Get column names from the R data frame
    col_names = list(col_names)
    # define the index.
    a = 1
    for col_name in col_names:
        col_name = str(col_name)
        # Get the expected data type from the PostgreSQL table schema
        expected_type = schema_dict.get(col_name, None)
        
        if expected_type is None:
            logging.warning(f"Column '{col_name}' not found in the database schema. Skipping conversion.")
            continue
        
        # Convert to the appropriate R type based on the expected PostgreSQL data type
        if 'date' in expected_type:
            # Convert to R's Date format
            try:
                # logging.info(f"converting {col_name} to R Date format {rdf.rx2[col_name]}")

                new_date = ymd(rdf.rx2(col_name))
                # rdf.rx2[col_name] = new_date    
                rdf = dplyr.mutate(rdf, **{col_name: new_date})
                # print(rdf.rx2(a))
                logging.info(f"Converted {col_name} to R Date format.")
            except Exception as e:
                logging.warning(f"Failed to convert {col_name} to Date: {e}")
            
        # elif 'int' in expected_type:
        #     # Convert to R integer
        #     try:
        #         rdf.rx2[col_name] = base.as_integer(rdf.rx2[col_name])
        #         logging.info(f"Converted {col_name} to R Integer.")
        #     except Exception as e:
        #         logging.warning(f"Failed to convert {col_name} to Integer: {e}")
        a += 1

    #     elif 'varchar' in expected_type or 'text' in expected_type:
    #         # Convert to R character (if needed, usually automatic)
    #         logging.info(f"Column {col_name} is already a string type. No conversion needed.")
    #     else:
    #         logging.info(f"No conversion rule for {col_name} (PostgreSQL type: {expected_type}). Skipping conversion.")
          
    return rdf


def load_csv_to_db(file_path, table_name, conn, schema):
    """
    Loads a CSV file into the specified database table in the given schema.

    Args:
        file_path (str): Path to the CSV file.
        table_name (str): Name of the database table.
        conn: Database connection object.
        schema (str): Database schema where the table is located.

    Raises:
        Exception: If any error occurs during the process.
    """
    try:
        # Adjust the parameters of read_csv based on your CSV file's format

        rdf = readr.read_delim(
            file=file_path,
            delim='\t',  # Change to the correct delimiter, e.g., '\t' for tab-delimited
            col_types=readr.cols(),  # Automatically detect column types
            progress=False
        )
        # Retrieve the table schema from PostgreSQL
        schema_dict = get_table_schema(conn, schema, table_name)

        # Compare and convert the data types based on the PostgreSQL table schema
        rdf = compare_and_convert_data_types(rdf, schema_dict)
        # rdf = readr.read_csv(
        #     file=file_path,
        #     col_types=readr.cols(),  # Automatically detect column types
        #     progress=False
        # )

        # Construct the fully qualified table name with schema
        fully_qualified_table_name = f'{schema}.{table_name}'

        # Insert data into the database table using DatabaseConnector
        # db_connector.insertTable(
        #     connection=conn,
        #     tableName=fully_qualified_table_name,
        #     data=rdf,
        #     dropTableIfExists=False,
        #     createTable=False,
        #     tempTable=False,
        #     progressBar=False,
        #     useMppBulkLoad=False
        # )

        logging.info(f"Loaded data into table '{fully_qualified_table_name}'.")

    except pd.errors.ParserError as e:
        logging.error(f"ParserError while reading '{file_path}': {e}")
        raise
    except Exception as e:
        logging.error(f"An error occurred while loading '{file_path}': {e}")
        raise

def load_all_csvs(folder_path, conn, schema):
    """
    Loads all CSV files from the specified folder into the database schema.

    Args:
        folder_path (str): Path to the folder containing CSV files.
        conn: Database connection object.
        schema (str): Database schema where the tables are located.

    Raises:
        Exception: If any error occurs during the process.
    """
    # Define the order of tables to be loaded based on dependencies
    table_order = [
        # 'vocabulary', 'domain', 'concept_class', 
        'concept',
        # 'relationship', 'concept_relationship', 'concept_ancestor', 'concept_synonym'
    ]

    # Map filenames to table names
    file_to_table_mapping = {
        # 'VOCABULARY.csv': 'vocabulary',
        # 'DOMAIN.csv': 'domain',
        # 'CONCEPT_CLASS.csv': 'concept_class',
        'CONCEPT.csv': 'concept',
        # 'RELATIONSHIP.csv': 'relationship',
        # 'CONCEPT_RELATIONSHIP.csv': 'concept_relationship',
        # 'CONCEPT_ANCESTOR.csv': 'concept_ancestor',
        # 'CONCEPT_SYNONYM.csv': 'concept_synonym'
    }

    missing_files = []

    for table in table_order:
        # Find the corresponding filename for the table
        filename = next(
            (fname for fname, tbl in file_to_table_mapping.items() if tbl == table),
            None
        )
        if filename:
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                try:
                    load_csv_to_db(file_path, table, conn, schema)
                except Exception as e:
                    logging.error(f"Failed to load data into table '{schema}.{table}': {e}")
                    raise
            else:
                logging.warning(f"File '{filename}' not found in folder '{folder_path}'. Skipping.")
                missing_files.append(filename)
        else:
            logging.warning(f"No CSV file mapped for table '{table}'. Skipping.")

    if missing_files:
        logging.warning(f"The following files were not found and were skipped: {missing_files}")

    logging.info("All available CSV files have been processed.")