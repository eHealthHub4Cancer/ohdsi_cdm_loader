from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError
import logging
from typing import Optional
import asyncio
from pg_bulk_loader import PgConnectionDetail, batch_insert_to_postgres
# Configure logging
logging.basicConfig(level=logging.INFO)

class DatabaseHandler:
    def __init__(self, dbms: Optional[str] = None , server: Optional[str] = None, user: Optional[str] = None, 
                 password: Optional[str] = None, database: Optional[str] = None, 
                 driver_path: Optional[str] = None, schema: Optional[str] = None, port: int=5432,
                 # Alias parameters
                 db_type: Optional[str] = None,
                 host: Optional[str] = None
                 ):
        """
        Initialize the DatabaseHandler with the given parameters.

        :param dbms: The database management system type.
        :param server: The server address.
        :param user: The username for database authentication.
        :param password: The password for database authentication.
        :param database: The name of the database.
        :param driver_path: Path to the database driver.
        :param port: This defines the port of the database.
        :param db_connector: Database connector object.
        """
     

        # Handle the alias parameters (map to the original parameter names)
        dbms = db_type if dbms is None else dbms 
        server = host if server is None else server

        # check for required parameters 
        if dbms is None or server is None or user is None or password is None or database is None or driver_path is None or schema is None:
            missing = []
            if dbms is None : missing.append("dbms/db_type")
            if server is None: missing.append("server/host")
            if user is None: missing.append("user")
            if password is None: missing.append("password")
            if database is None: missing.append("database")
            if driver_path is None: missing.append("driver_path")
            if schema is None: missing.append("schema")
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        
        self._dbms = dbms
        self._server = server
        self._user = user
        self._password = password
        self._database = database
        self._driver_path = driver_path
        self._db_connector = importr('DatabaseConnector')
        self._conn: Optional[object] = None
        self._conn_details: Optional[object] = None
        self._common_data_model = importr('CommonDataModel')
        self._port = port
        self._schema = schema
        self.create_bulk_connection()

    def create_bulk_connection(self):
        # Create Postgres Connection Details object. This will help in creating and managing the database connections 
        self.pg_conn_details = PgConnectionDetail(
            user=self._user,
            password=self._password,
            database=self._database,
            host=self._server,
            port=self._port,
            schema=self._schema
        )
    
    def get_bulk_connection(self):
        return self.pg_conn_details

    # Getters and Setters
    def get_dbms(self) -> str:
        """Get the database management system type."""
        return self._dbms

    def set_dbms(self, dbms: str) -> None:
        """Set the database management system type."""
        self._dbms = dbms

    def set_port(self, port: int) -> None:
        """set the database port"""
        self._port = port

    def get_port(self) -> int:
        """get the database port"""
        return self._port
    
    def get_server(self) -> str:
        """Get the server address."""
        return self._server

    def set_server(self, server: str) -> None:
        """Set the server address."""
        self._server = server

    def get_user(self) -> str:
        """Get the username for database authentication."""
        return self._user

    def set_user(self, user: str) -> None:
        """Set the username for database authentication."""
        self._user = user

    def get_password(self) -> str:
        """Get the password for database authentication."""
        return self._password

    def set_password(self, password: str) -> None:
        """Set the password for database authentication."""
        self._password = password

    def get_database(self) -> str:
        """Get the name of the database."""
        return self._database

    def set_database(self, database: str) -> None:
        """Set the name of the database."""
        self._database = database

    def get_driver_path(self) -> str:
        """Get the path to the database driver."""
        return self._driver_path
    
    def set_connection(self, conn) -> None:
        """set the connection"""
        self._conn = conn

    def get_connection(self) -> object:
        """Return the connection which has been set"""
        return self._conn
    
    def get_db_connector(self) -> object:
        """Returns the connector object"""
        return self._db_connector

    def set_driver_path(self, driver_path: str) -> None:
        """Set the path to the database driver."""
        self._driver_path = driver_path

    def set_connect_details(self, connect_details) -> None:
        """set the connection details"""
        self._conn_details = connect_details

    def set_schema(self, schema: str) -> None:
        """Set the database schema."""
        self._schema = schema

    def connect_to_db(self) -> object:
        """
        Establish a connection to the database.

        :raises Exception: If there is an error creating the database connection.
        """
        try:
            connection_details = self._db_connector.createConnectionDetails(
                dbms=self._dbms,
                server=f"{self._server}/{self._database}",
                user=self._user,
                password=self._password,
                pathToDriver=self._driver_path,
                port=self._port
            )
            self._conn = self._db_connector.connect(connection_details)
            logging.info("Database connection established successfully.")
            self.set_connect_details(connection_details)
            self.set_connection(self._conn)
            return self._conn
            
        except RRuntimeError as e:
            raise Exception(f"Error creating database connection: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while creating the database connection: {e}")

    def disable_foreign_key_checks(self, table) -> None:
        """
        Disable foreign key checks in the database.

        :raises Exception: If there is an error disabling foreign key checks.
        """
        try:
            # query = "SET session_replication_role = 'replica';"
            query = f"ALTER TABLE {self._schema}.{table} DISABLE TRIGGER ALL;"
            self._db_connector.executeSql(self._conn, query)
            logging.info("Foreign key checks disabled.")
        except Exception as e:
            raise Exception(f"Failed to disable foreign key checks: {e}")

    def enable_foreign_key_checks(self) -> None:
        """
        Enable foreign key checks in the database.

        :raises Exception: If there is an error enabling foreign key checks.
        """
        try:
            query = "SET session_replication_role = 'origin';"
            self._db_connector.executeSql(self._conn, query)
            logging.info("Foreign key checks enabled.")
        except Exception as e:
            raise Exception(f"Failed to enable foreign key checks: {e}")

    def empty_table(self, schema: str, table_name: str) -> None:
        """
        Truncate the specified table in the database.

        :param schema: The schema containing the table.
        :param table_name: The name of the table to truncate.
        :raises Exception: If there is an error truncating the table.
        """
        try:
            query = f"TRUNCATE {schema}.{table_name} CASCADE;"
            self._db_connector.executeSql(self._conn, query)
            logging.info(f"Table '{schema}.{table_name}' truncated successfully.")
        except Exception as e:
            raise Exception(f"Failed to truncate table '{schema}.{table_name}': {e}")

    def execute_ddl(self, cdm_version: str) -> None:
        """
        Execute the Common Data Model (CDM) DDL script.
        :param cdm_version: The version of the CDM to execute.
        :param cdm_database_schema: The database schema for the CDM.
        :raises Exception: If there is an error executing the CDM DDL.
        """
        if not self._conn_details:
            raise Exception("Connection details are not set. Connect to the database first.")

        try:
            self._common_data_model.executeDdl(
                connectionDetails=self._conn_details,
                cdmVersion=cdm_version,
                cdmDatabaseSchema=self._schema
            )
            logging.info("CDM DDL execution completed successfully.")
        except RRuntimeError as e:
            raise Exception(f"Error executing CDM DDL: {e}")
        
    def create_cdm_schema(self, schema: str) -> None:
        """
        Create the Common Data Model (CDM) schema in the database.
        :param schema: The schema to create for the CDM.
        :raises Exception: If there is an error creating the CDM schema.
        """
        try:
            query = f"CREATE SCHEMA IF NOT EXISTS {schema};"
            self._db_connector.executeSql(self._conn, query)
            logging.info(f"CDM schema '{schema}' created successfully.")
        except Exception as e:
            raise Exception(f"Error creating CDM schema '{schema}': {e}")
        
   