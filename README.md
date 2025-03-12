# OHDSI CDM Data Loader

This repository provides scripts to load Common Data Model (CDM) data from OHDSI's standardized vocabularies (version 5.4 or 5.3) into CDM tables in a relational database. It is designed for the OHDSI community and those working with OHDSI's Common Data Model for large-scale observational research.

This project has been primarily tested with PostgreSQL. We hope to expand across other databases supported within the OHDSI community in upcoming versions.

## Requirements

### Python and Database Requirements

- Python 3.9
- PostgreSQL database, still checking for others.
- Required Python libraries (listed in `requirements.txt`)

### R Requirements

Some of the processes and dependencies in the OHDSI environment may require specific R packages to interact with the OHDSI CDM and tools. Ensure the following R packages are installed:

```r
# Install OHDSI-specific R packages
install.packages("devtools")
install.packages("DatabaseConnector")
install.packages("SqlRender")
devtools::install_github("OHDSI/CommonDataModel")  # For working with CDM-related functionality
install.packages("arrow")
```

## Install Python Dependencies

To install the Python dependencies listed in `requirements.txt`, run the following command:

```bash
pip install -r requirements.txt
```

### for flexibility and avoiding compromise with other packages, we advise creating a virtual environment or using docker.

## Files

### 1. `db_connector.py`

This script contains the `DatabaseHandler` class, which manages connections to a PostgreSQL database.

#### Key Features:
- Establishes a connection to the CDM database (primarily tested with PostgreSQL).
- Executes SQL commands and handles transactions for the CDM tables.

#### Example (Python):

```python
from db_connector import DatabaseHandler

database_connector = DatabaseHandler(
    db_type="postgresql",  # Database type (e.g., postgresql)
    host="localhost",      # Database host
    user="postgres",       # Database user
    password="your_password",  # Database password
    database="ohdsi_cdm",  # OHDSI CDM database
    driver_path="path_to_driver"  # path to driver for selected database
    schema="schema" # schema for holding the database table.-- make sure it is set.
    port=port # integer that defines the port, 5432 is used if not specified.
)

### connection to the database.
db_conn = database_connector.connect_to_db()

if db_conn:
    print("Connected to the database successfully!")
else:
    print("Failed to connect to the database.")
```

### 2. `load_csv.py`

This script loads the OHDSI CDM vocabularies (version 5.3 or 5.4) from CSV files into the CDM tables in the database.

#### Key Features:
- Loads all CSV files for the standardized vocabularies from the specified directory into the corresponding create database. For clarity the tables can be created using the execute_ddl function from the commondatamodel package. 

#### Prerequisites
Before using the DatabaseHandler:

1. **Download vocabulary files**: Get the latest OHDSI standardized vocabularies from [OHDSI Athena](https://athena.ohdsi.org/vocabulary/list)

2. **Download database drivers**: Obtain the appropriate JDBC driver for PostgreSQL database from [DatabaseConnector documentation](https://ohdsi.github.io/DatabaseConnector/articles/Connecting.html)

```python
from db_connector import DatabaseHandler

# Initialize the database connection
database_connector = DatabaseHandler(
    db_type="postgresql",  # Database type (e.g., postgresql)
    host="localhost",      # Database host
    user="postgres",       # Database user
    password="your_password",  # Database password
    database="ohdsi_cdm",  # OHDSI CDM database
    driver_path="path_to_driver"  # path to driver for selected database
    schema="schema" # schema for holding the database table.-- make sure it is set.
    port=port # integer that defines the port, 5432 is used if not specified.
)

# Connect to the CDM database
db_conn = database_connector.connect_to_db()
# generate the table in the database
database_connector.execute_ddl(cdm_version = "value")
```
- Uses the active database connection and CDM-compliant table structure.

#### Example (Python):

```python
from load_csv import CSVLoader

csv_loader = CSVLoader(
    db_connection=db_conn,  # Active database connection
    database_handler=database_connector
)

csv_loader.load_all_csvs("path_to_downloaded_csv_directory")
```

### 3. `main.py`

This is the main entry point of the application. It integrates the database connection and CSV loading functionality specifically for OHDSI's CDM.

#### Usage:

The script connects to the CDM database and loads all relevant CDM data from OHDSI’s standardized vocabularies (versions 5.3 or 5.4).
#### Workflow in Main Script:
#### Environment Variables

To ensure security and flexibility, it is recommended to store database credentials as environment variables rather than hardcoding them into the script.

Here’s an example of how to set environment variables:

```bash
- `DB_PORT`: The port number for the database.
- `DB_TYPE`: The type of the database (e.g., `postgresql`, `mysql`).
- `DB_SERVER`: The server address of the database.
- `DB_NAME`: The name of the database.
- `DB_PASSWORD`: The password for the database user.
- `DB_USER`: The username for the database.
- `DRIVER_PATH`: The path to the database driver.
- `DB_SCHEMA`: The schema name in the database.
- `CSV_PATH`: The path to the CSV file to be loaded.
- `CDM_VERSION`: The version of the Common Data Model (CDM).

```

Update the script to read these variables using `os.getenv`:

```python
import os
from dotenv import load_dotenv
from db_connector import DatabaseHandler
from load_csv import CSVLoader

load_dotenv()


database_connector = DatabaseHandler(
    db_type=os.getenv('DB_TYPE'),
    host=os.getenv('DB_SERVER'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    driver_path=os.getenv('DRIVER_PATH'),
    schema=os.getenv('DB_SCHEMA'),
    port=os.getenv('DB_PORT')
)

db_conn = database_connector.connect_to_db()
csv_loader = CSVLoader(db_conn, database_connector)
csv_loader.load_all_csvs(os.get('CSV_PATH'))

# to create the cdm tables.
database_connector.execute_ddl(os.get('CDM_VERSION'))
```


## Credits

This project is designed to work with OHDSI's Common Data Model (CDM) and standardized vocabularies. The tools and processes used here are compatible with OHDSI standards, and the database loader has been tested specifically for PostgreSQL, though it should work with other databases supported by OHDSI. 

<a href="https://ohdsi.org">
  <img src="https://res.cloudinary.com/dc29czhf9/image/upload/v1729287157/h243-ohdsi-logo-with-text_hhymri.png" alt="OHDSI" width="100"/>
</a>

**OHDSI** (Observational Health Data Sciences and Informatics) is a multi-stakeholder, interdisciplinary collaborative that aims to bring out the value of observational health data through large-scale analytics. Learn more about OHDSI and the CDM on the [official OHDSI website](https://ohdsi.org).

<a href="https://ehealth4cancer.org">
  <img src="https://res.cloudinary.com/dc29czhf9/image/upload/v1729287084/download_umxgmo.jpg" alt="eHealth Hub Limerick" width="100"/>
</a>

This project was also supported by **eHealth Hub Limerick**, contributing to the development and deployment of health data tools for innovative healthcare solutions. Learn more about eHealth Hub Limerick at [eHealth Hub Limerick's official website](https://ehealth4cancer.org).


## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.