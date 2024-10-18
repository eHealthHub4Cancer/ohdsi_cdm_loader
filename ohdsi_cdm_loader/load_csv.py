import os
import pandas as pd
import rpy2.robjects as robjs
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError
from .db_connector import disable_foreign_key_checks, enable_foreign_key_checks, empty_table
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Declare global variables outside the function
db_connector = None
readr = None
base = None
lubridate = None
ymd = None
dplyr = None

# Import relevant R packages with exception handling
def load_packages() -> None:
    """
    Loads the required R packages using rpy2 and sets them as global variables.

    Raises:
        ImportError: If an error occurs while importing the R packages.
    """
    global db_connector, readr, base, lubridate, ymd, dplyr
    try:
        db_connector = importr('DatabaseConnector')
        readr = importr('readr')
        base = importr('base')
        lubridate = importr('lubridate')
        ymd = lubridate.ymd
        dplyr = importr('dplyr')
    except RRuntimeError as e:
        raise ImportError(f"Failed to import R package: {e}")

def get_table_schema(conn: object, schema: str, table_name: str) -> dict:
    """
    Retrieve column names and data types from the target PostgreSQL table.

    Args:
        conn (object): Database connection object.
        schema (str): Database schema name.
        table_name (str): Name of the table.

    Returns:
        dict: A dictionary with column names as keys and data types as values.
    """
    query = f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = '{table_name}';
    """
    # Execute the query
    result = db_connector.querySql(conn, query)
    
    # Extract schema information into a dictionary
    colnames = robjs.r.colnames(result)
    data = {col_name: list(result.rx2(col_name)) for col_name in colnames}
    return dict(zip(data['column_name'], data['data_type']))

def compare_and_convert_data_types(rdf: object, schema_dict: dict) -> object:
    """
    Compare the data frame columns with the database schema and convert columns as necessary.

    Args:
        rdf (object): R data frame to be compared and converted.
        schema_dict (dict): Dictionary containing column names and expected data types.

    Returns:
        object: The modified R data frame with converted data types.
    """
    for col_name in base.colnames(rdf):
        col_name = str(col_name)
        expected_type = schema_dict.get(col_name)

        if not expected_type:
            logging.warning(f"Column '{col_name}' not found in database schema. Skipping conversion.")
            continue

        try:
            if 'date' in expected_type:
                rdf = dplyr.mutate(rdf, **{col_name: ymd(rdf.rx2(col_name))})
                logging.info(f"Converted '{col_name}' to R Date format.")
            elif 'int' in expected_type:
                rdf = dplyr.mutate(rdf, **{col_name: base.as_integer(rdf.rx2(col_name))})
                logging.info(f"Converted '{col_name}' to R Integer.")
            elif 'char' in expected_type or 'text' in expected_type:
                logging.info(f"Column '{col_name}' is already a string type. No conversion needed.")
            else:
                logging.info(f"No conversion rule for '{col_name}' (type: {expected_type}). Skipping.")
        except Exception as e:
            logging.warning(f"Failed to convert '{col_name}': {e}")

    return rdf

def load_csv_to_db(file_path: str, table_name: str, conn: object, schema: str) -> None:
    """
    Load a CSV file into the specified database table.

    Args:
        file_path (str): Path to the CSV file.
        table_name (str): Name of the database table.
        conn (object): Database connection object.
        schema (str): Database schema name.

    Returns:
        None
    """
    try:
        disable_foreign_key_checks(conn, db_connector)
        # empty the table.
        empty_table(conn, db_connector, schema, table_name)
        # Load CSV into R dataframe
        rdf = readr.read_delim(file=file_path, delim='\t', col_types=readr.cols(), 
        na=robjs.r("character(0)"), progress=False)
        # Retrieve the schema from the database
        schema_dict = get_table_schema(conn, schema, table_name)
        # Convert data types
        rdf = compare_and_convert_data_types(rdf, schema_dict)
        # Insert data into database
        db_connector.insertTable(
            connection=conn,
            tableName=f'{schema}.{table_name}',
            data=rdf,
            dropTableIfExists=False,
            createTable=False,
            tempTable=False,
            progressBar=True,
            useMppBulkLoad=False
        )
        enable_foreign_key_checks(conn, db_connector)
        logging.info(f"Loaded data into table '{schema}.{table_name}'.")

    except Exception as e:
        raise RuntimeError(f"Error loading '{file_path}' into '{table_name}': {e}")

def load_all_csvs(folder_path: str, conn: object, schema: str) -> None:
    """
    Load all CSV files from the specified folder into the database schema.

    Args:
        folder_path (str): Path to the folder containing CSV files.
        conn (object): Database connection object.
        schema (str): Database schema name.

    Returns:
        None
    """
    table_order = [
        'vocabulary', 'domain', 'concept_class', 'concept',
        'relationship', 'concept_relationship', 'concept_ancestor',
        'concept_synonym', 'drug_strength'
    ]

    file_to_table_mapping = {
        'VOCABULARY.csv': 'vocabulary',
        'DOMAIN.csv': 'domain',
        'CONCEPT_CLASS.csv': 'concept_class',
        'CONCEPT.csv': 'concept',
        'RELATIONSHIP.csv': 'relationship',
        'CONCEPT_RELATIONSHIP.csv': 'concept_relationship',
        'CONCEPT_ANCESTOR.csv': 'concept_ancestor',
        'CONCEPT_SYNONYM.csv': 'concept_synonym',
        'DRUG_STRENGTH.csv': 'drug_strength'
    }

    missing_files = []

    for table in table_order:
        filename = next((fname for fname, tbl in file_to_table_mapping.items() if tbl == table), None)
        if filename:
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                try:
                    load_csv_to_db(file_path, table, conn, schema)
                except Exception as e:
                    raise RuntimeError(f"Failed to load '{filename}' into '{table}': {e}")
            else:
                logging.warning(f"File '{filename}' not found in folder '{folder_path}'.")
                missing_files.append(filename)
        else:
            logging.warning(f"No CSV file mapped for table '{table}'.")

    if missing_files:
        logging.warning(f"Missing files: {missing_files}")

    logging.info("All CSV files have been processed.")