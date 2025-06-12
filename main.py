from ohdsi_cdm_loader.db_connector import DatabaseHandler
from ohdsi_cdm_loader.load_csv import CSVLoader
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

# Set the values from the environment. These are typically configured in a
# `.env` file or passed in via Docker.
db_port = os.getenv("DB_PORT", "5432")
db_type = os.getenv("DB_TYPE", "postgresql")
db_server = os.getenv("DB_SERVER", "localhost")
db_name = os.getenv("DB_NAME")
db_password = os.getenv("DB_PASSWORD")
db_user = os.getenv("DB_USER")
driver_path = os.getenv("DRIVER_PATH", "/jdbc").strip()
db_schema = os.getenv("DB_SCHEMA", "public")  # CDM schema
csv_path = os.getenv("CSV_PATH", "/csv").strip()
cdm_version = os.getenv("CDM_VERSION", "5.4")
synthea_version = os.getenv("SYNTHEA_VERSION", "3.0")
synthea_schema = os.getenv("SYNTHEA_SCHEMA", "synthea")
synthea_csv = os.getenv("SYNTHEA_CSV")

# Validate required environment variables
required_vars = {
    "DB_NAME": db_name,
    "DB_USER": db_user,
    "DB_PASSWORD": db_password,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Validate paths exist
if not os.path.exists(csv_path):
    print(f"Error: CSV path does not exist: {csv_path}")
    sys.exit(1)

if not os.path.exists(driver_path):
    print(f"Warning: Driver path does not exist: {driver_path}")

synthea_order = [
    'allergies', 'careplans', 'conditions',
    'devices', 'encounters', 'imaging_studies',
    'immunizations', 'medications', 'observations',
    'organizations', 'patients', 'payer_transitions',
    'payers', 'procedures', 'providers', 'supplies'
]

cdm_order = ['vocabulary', 'domain', 
             'concept_class', 'relationship', 
             'drug_strength',  'concept_synonym', 
             'concept', 'concept_relationship', 
            'concept_ancestor']

def main():
    """Entry point for running the CDM loader."""
    print("=== OHDSI CDM Loader Starting ===")
    print(f"Database: {db_type}://{db_server}:{db_port}/{db_name}")
    print(f"Schema: {db_schema}")
    print(f"CSV Path: {csv_path}")
    print(f"Driver Path: {driver_path}")
    print(f"CDM Version: {cdm_version}")
    print("=" * 40)
    
    try:
        database_connector = DatabaseHandler(
            db_type=db_type,
            host=db_server,
            user=db_user,
            password=db_password,
            database=db_name,
            driver_path=driver_path,
            schema=db_schema,
            port=int(db_port),
        )

        print("Connecting to database...")
        db_conn = database_connector.connect_to_db()
        print("✓ Database connection successful")

        # ------------------------------------------------------------------
        # 1. Create the CDM tables and load the vocabulary CSV files
        # ------------------------------------------------------------------
        print(f"\n1. Creating CDM tables (version {cdm_version})...")
        database_connector.execute_ddl(cdm_version)
        print("✓ CDM tables created")

        print(f"\n2. Loading vocabulary CSV files from {csv_path}...")
        csv_loader = CSVLoader(db_connection=db_conn, database_handler=database_connector)
        csv_loader.load_all_csvs(csv_path, cdm_order, upper=False, batch_size=10000)
        print("✓ Vocabulary CSV files loaded")

        # ------------------------------------------------------------------
        # 2. Create the Synthea tables and load the Synthea CSV files
        # ------------------------------------------------------------------
        # if synthea_csv and os.path.exists(synthea_csv):
        #     print(f"\n3. Creating Synthea tables (version {synthea_version})...")
        #     database_connector.create_synthea_tables(synthea_schema, synthea_version)
        #     database_connector.set_schema(synthea_schema)
        #     print("✓ Synthea tables created")
            
        #     print(f"4. Loading Synthea CSV files from {synthea_csv}...")
        #     csv_loader.load_all_csvs(synthea_csv, synthea_order, upper=False, synthea=True)
        #     print("✓ Synthea CSV files loaded")
        # else:
        #     print(f"\n3. Skipping Synthea loading (path not provided or doesn't exist: {synthea_csv})")

        # ------------------------------------------------------------------
        # 3. Run additional ETL helpers
        # ------------------------------------------------------------------
        # Uncomment these as needed:
        
        # print("\n5. Creating map and rollup tables...")
        # database_connector.create_map_and_rollup_tables(
        #     cdm_schema=db_schema,
        #     cdm_version=cdm_version,
        #     synthea_schema=synthea_schema,
        #     synthea_version=synthea_version,
        # )
        # print("✓ Map and rollup tables created")

        # print("\n6. Creating indices...")
        # database_connector.create_indices(
        #     cdm_schema=db_schema,
        #     synthea_schema=synthea_schema,
        #     synthea_version=synthea_version,
        # )
        # print("✓ Indices created")

        # print("\n7. Loading events...")
        # database_connector.load_events(
        #     cdm_schema=db_schema,
        #     cdm_version=cdm_version,
        #     synthea_schema=synthea_schema,
        #     synthea_version=synthea_version,
        # )
        # print("✓ Events loaded")

        print("\n=== CDM Loader completed successfully! ===")

    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        sys.exit(1)
    
    finally:
        # Close database connection if it exists
        try:
            if 'db_conn' in locals():
                db_conn.close()
                print("Database connection closed.")
        except Exception as e:
            print(f"Warning: Could not close database connection: {e}")

if __name__ == "__main__":
    main()