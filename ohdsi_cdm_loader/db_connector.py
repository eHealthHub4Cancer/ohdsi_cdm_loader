from rpy2 import robjects as robs
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError

# Import relevant R packages with exception handling
def load_packages():
    try:
        sql_render = importr('SqlRender')
        db_connector = importr('DatabaseConnector')
        return sql_render, db_connector
    except RRuntimeError as e:
        raise Exception("Error importing R packages 'SqlRender' or 'DatabaseConnector' {e}")

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

# load the packages.
sql_rend, db_conn = load_packages()

connect_to_db("postgresql", "localhost", "postgres", "Daybme20@me", "ohdsi", "C:/Users/23434813/Desktop/AML data/ohdsi/", db_conn)
