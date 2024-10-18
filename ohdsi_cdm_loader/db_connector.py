from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

class DatabaseHandler:
    def __init__(self, dbms: str, server: str, user: str, password: str, database: str, driver_path: str, db_connector: object):
        """
        Initialize the DatabaseHandler with the given parameters.

        :param dbms: The database management system type.
        :param server: The server address.
        :param user: The username for database authentication.
        :param password: The password for database authentication.
        :param database: The name of the database.
        :param driver_path: Path to the database driver.
        :param db_connector: Database connector object.
        """
        self._dbms = dbms
        self._server = server
        self._user = user
        self._password = password
        self._database = database
        self._driver_path = driver_path
        self._db_connector = db_connector
        self._conn: Optional[object] = None
        self._common_data_model = importr('CommonDataModel')

    # Getters and Setters
    def get_dbms(self) -> str:
        """Get the database management system type."""
        return self._dbms

    def set_dbms(self, dbms: str) -> None:
        """Set the database management system type."""
        self._dbms = dbms

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

    def set_driver_path(self, driver_path: str) -> None:
        """Set the path to the database driver."""
        self._driver_path = driver_path

    def connect_to_db(self) -> None:
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
                pathToDriver=self._driver_path
            )
            self._conn = self._db_connector.connect(connection_details)
            logging.info("Database connection established successfully.")
        except RRuntimeError as e:
            raise Exception(f"Error creating database connection: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while creating the database connection: {e}")

    def disable_foreign_key_checks(self) -> None:
        """
        Disable foreign key checks in the database.

        :raises Exception: If there is an error disabling foreign key checks.
        """
        try:
            query = "SET session_replication_role = 'replica';"
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
            query = f"TRUNCATE {schema}.{table_name};"
            self._db_connector.executeSql(self._conn, query)
            logging.info(f"Table '{schema}.{table_name}' truncated successfully.")
        except Exception as e:
            raise Exception(f"Failed to truncate table '{schema}.{table_name}': {e}")

    def execute_ddl(self, cdm_version: str, cdm_database_schema: str) -> None:
        """
        Execute the Common Data Model (CDM) DDL script.

        :param cdm_version: The version of the CDM to execute.
        :param cdm_database_schema: The database schema for the CDM.
        :raises Exception: If there is an error executing the CDM DDL.
        """
        try:
            common_data_model = self._common_data_model
            common_data_model.executeDdl(
                connectionDetails=self._conn,
                cdmVersion=cdm_version,
                cdmDatabaseSchema=cdm_database_schema
            )
            logging.info("CDM DDL execution completed.")
        except RRuntimeError as e:
            raise Exception(f"Error executing CDM DDL: {e}")