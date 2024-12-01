from ohdsi_cdm_loader.db_connector import DatabaseHandler
from ohdsi_cdm_loader.load_csv import CSVLoader
from dotenv import load_dotenv
import os

load_dotenv()

# set the values.
db_port = os.getenv('DB_PORT')
db_type = os.getenv('DB_TYPE')
db_server = os.getenv('DB_SERVER')
db_name = os.getenv('DB_NAME')
db_password = os.getenv('DB_PASSWORD')
db_user = os.getenv('DB_USER')
driver_path = os.getenv('DRIVER_PATH')
db_schema = os.getenv('DB_SCHEMA')
csv_path = os.getenv('CSV_PATH')
cdm_version = os.getenv('CDM_VERSION')

def main():
    database_connector = DatabaseHandler(
        db_type, db_server, db_user,
        db_password, db_name, driver_path,
        db_schema, db_port
    )
    db_conn = database_connector.connect_to_db()
    # database_connector.execute_ddl("5.4", "aml_practice")
    csv_loader = CSVLoader(db_conn, database_connector)
    csv_loader.load_all_csvs(csv_path)

if __name__ == "__main__":
    main()

