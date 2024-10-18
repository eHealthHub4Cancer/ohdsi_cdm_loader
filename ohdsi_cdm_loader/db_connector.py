from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class DatabaseHandler:
    def __init__(self, dbms: str, server: str, user: str, password: str, database: str, driver_path: str, db_connector: object):
        self._dbms = dbms
        self._server = server
        self._user = user
        self._password = password
        self._database = database
        self._driver_path = driver_path
        self._db_connector = db_connector
        self._conn = None
        self._common_data_model = importr('CommonDataModel')

    # Getters and Setters
    def get_dbms(self):
        return self._dbms

    def set_dbms(self, dbms: str):
        self._dbms = dbms

    def get_server(self):
        return self._server

    def set_server(self, server: str):
        self._server = server

    def get_user(self):
        return self._user

    def set_user(self, user: str):
        self._user = user

    def get_password(self):
        return self._password

    def set_password(self, password: str):
        self._password = password

    def get_database(self):
        return self._database

    def set_database(self, database: str):
        self._database = database

    def get_driver_path(self):
        return self._driver_path

    def set_driver_path(self, driver_path: str):
        self._driver_path = driver_path

    def connect_to_db(self):
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

    def disable_foreign_key_checks(self):
        try:
            query = "SET session_replication_role = 'replica';"
            self._db_connector.executeSql(self._conn, query)
            logging.info("Foreign key checks disabled.")
        except Exception as e:
            raise Exception(f"Failed to disable foreign key checks: {e}")

    def enable_foreign_key_checks(self):
        try:
            query = "SET session_replication_role = 'origin';"
            self._db_connector.executeSql(self._conn, query)
            logging.info("Foreign key checks enabled.")
        except Exception as e:
            raise Exception(f"Failed to enable foreign key checks: {e}")

    def empty_table(self, schema: str, table_name: str):
        try:
            query = f"TRUNCATE {schema}.{table_name};"
            self._db_connector.executeSql(self._conn, query)
            logging.info(f"Table '{schema}.{table_name}' truncated successfully.")
        except Exception as e:
            raise Exception(f"Failed to truncate table '{schema}.{table_name}': {e}")

    def execute_ddl(self, cdm_version, cdm_database_schema):
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