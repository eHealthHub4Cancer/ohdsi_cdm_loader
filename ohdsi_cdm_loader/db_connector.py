from rpy2 import robjects as robs
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import relevant R packages with exception handling
def load_packages():
    try:
        db_connector = importr('DatabaseConnector')
        return db_connector
    except RRuntimeError as e:
        raise Exception("Error importing R package 'DatabaseConnector' {e}")

# Function to create a connection to the database using DatabaseConnector in R
def connect_to_db(dbms: str, server: str, user: str, password: str, database: str, driver_path: str, db_connector):
    """
    Creates a connection to the database using DatabaseConnector in R.

    Args:
        dbms (str): The database type (e.g., 'postgresql', 'sql server')
        server (str): The server address (e.g., 'localhost' or IP address)
        user (str): The username for the database
        password (str): The password for the database user
        database (str): The name of the database (schema),
        driver_path(str): path to driver.
        db_connector (DatabaseConnector) : connector library


    Returns:
        R object representing the database connection

    Raises:
        Exception: If unable to create the database connection
    """
    try:
        # Create connection details using DatabaseConnector
        connection_details = db_connector.createConnectionDetails(
            dbms=dbms,
            server=f"{server}/{database}",
            user=user,
            password=password,
            pathToDriver = driver_path
        )
        # Establish the connection
        conn = db_connector.connect(connection_details)
        print("Database connection established successfully.")
        return conn
    except RRuntimeError as e:
        raise Exception(f"Error creating database connection {e}")

    except Exception as e:
        raise Exception(f"An unexpected error occurred while creating the database connection {e}")

def disable_foreign_key_checks(conn, db_connector):
    """
    Disables foreign key checks in PostgreSQL for the current session.
    
    Args:
        conn: Database connection object.
    """
    try:
        query = "SET session_replication_role = 'replica';"
        db_connector.executeSql(conn, query)
        logging.info("Foreign key checks disabled.")
    except Exception as e:
        raise Exception(f"Failed to disable foreign key checks: {e}")
        

def enable_foreign_key_checks(conn, db_connector):
    """
    Enables foreign key checks in PostgreSQL for the current session.
    
    Args:
        conn: Database connection object.
    """
    try:
        query = "SET session_replication_role = 'origin';"
        db_connector.executeSql(conn, query)
        logging.info("Foreign key checks enabled.")
    except Exception as e:
        raise Exception(f"Failed to enable foreign key checks: {e}")

# load the packages.
db_conn = load_packages()

get_conn = connect_to_db("postgresql", "localhost", "postgres", "Daybme20@me", "ohdsi", "C:/Users/23434813/Desktop/AML data/ohdsi/", db_conn)
