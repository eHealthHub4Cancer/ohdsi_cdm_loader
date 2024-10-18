from ohdsi_cdm_loader.db_connector import DatabaseHandler
from ohdsi_cdm_loader.load_csv import CSVLoader

# load the packages.


database_connector = DatabaseHandler("postgresql", "localhost", "postgres", "Daybme20@me", "ohdsi", "C:/Users/23434813/Desktop/AML data/ohdsi/")
db_conn = database_connector.connect_to_db()

# csv_loader = CSVLoader()

# get_conn = connect_to_db("postgresql", "localhost", "postgres", "Daybme20@me", "ohdsi", "C:/Users/23434813/Desktop/AML data/ohdsi/", db_conn)

# load_all_csvs("C:/Users/23434813/Desktop/latest_vocabularies/voc_20240701_v5/", get_conn, "ohdsi_practice")