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
synthea_version = os.getenv('SYNTHEA_VERSION')
synthea_schema = os.getenv('SYNTHEA_SCHEMA')
synthea_csv = os.getenv('SYNTHEA_CSV')

synthea_order = [
    'allergies', 'careplans', 'conditions',
    'devices', 'encounters', 'imaging_studies',
    'immunizations', 'medications', 'observations',
    'organizations', 'patients', 'payer_transitions',
    'payers','procedures', 'providers', 'supplies'
    ]

cdm_order =[
    'vocabulary', 'domain',
    'concept_class', 'concept',
    'relationship', 'concept_relationship', 
    'concept_ancestor', 'concept_synonym', 
    'drug_strength']

def main():
    database_connector = DatabaseHandler(
     db_type=db_type, host=db_server, user=db_user,
     password=db_password, database=db_name, driver_path=driver_path,
     schema=synthea_schema, port=db_port
    )
    db_conn = database_connector.connect_to_db()
    # database_connector.execute_ddl("5.4", "aml_practice")
    database_connector.set_schema(synthea_schema)
    csv_loader = CSVLoader(db_connection=db_conn, database_handler=database_connector)
    csv_loader.load_all_csvs(synthea_csv, synthea_order, upper=False, synthea=True)

    database_connector.create_map_and_rollup_tables(
        cdm_schema=db_schema, cdm_version=cdm_version,
        synthea_schema=synthea_schema, synthea_version=synthea_version
    )
    database_connector.create_indices(
        cdm_schema=db_schema, synthea_schema=synthea_schema, synthea_version=synthea_version
    )
    database_connector.load_events(
        cdm_schema=db_schema, cdm_version=cdm_version,
        synthea_schema=synthea_schema, synthea_version=synthea_version
    )

    # create synthea tables.
    # database_connector.create_synthea_tables(synthea_schema, synthea_version)

if __name__ == "__main__":
    main()

