from ohdsi_cdm_loader.db_connector import connect_to_db, load_packages
from ohdsi_cdm_loader.load_csv import load_all_csvs, load_csv_to_db

# load the packages.
db_conn = load_packages()

get_conn = connect_to_db("postgresql", "localhost", "postgres", "Daybme20@me", "ohdsi", "C:/Users/23434813/Desktop/AML data/ohdsi/", db_conn)

load_all_csvs("C:/Users/23434813/Desktop/latest_vocabularies/voc_20240701_v5/", get_conn, "ohdsi_practice")