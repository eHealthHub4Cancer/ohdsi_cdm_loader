# OHDSI CDM Data Loader

This repository provides scripts to load Common Data Model (CDM) data from OHDSI's standardized vocabularies (version 5.4 or 5.3) into CDM tables in a relational database. It is designed for the OHDSI community and those working with OHDSI's Common Data Model for large-scale observational research.

Although this project has been primarily tested with PostgreSQL, it may also work with other supported databases by OHDSI (still testing).

## Requirements

### Python Requirements

- Python 3.x
- PostgreSQL database (for testing, but adaptable for other OHDSI-supported databases)
- Required Python libraries (listed in `requirements.txt`)

### R Requirements

Some of the processes and dependencies in the OHDSI environment may require specific R packages to interact with the OHDSI CDM and tools. Ensure the following R packages are installed:

```r
# Install OHDSI-specific R packages
install.packages("devtools")
install.packages("DatabaseConnector")
install.packages("SqlRender")
devtools::install_github("OHDSI/CommonDataModel")  # For working with CDM-related functionality

# some other packages (not OHDSI specific)
install.packages("lubridate")
install.packages("dplyr")
install.packages("readr")
```

## Install Python Dependencies

To install the Python dependencies listed in `requirements.txt`, run the following command:

```bash
pip install -r requirements.txt
```

## Files

### 1. `db_connector.py`

This script contains the `DatabaseHandler` class, which manages connections to a PostgreSQL database and can be adapted to other OHDSI-supported databases.

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
)

db_conn = database_connector.connect_to_db()

if db_conn:
    print("Connected to the database successfully!")
else:
    print("Failed to connect to the database.")
```

### 2. `load_csv.py`

This script loads the OHDSI CDM vocabularies (version 5.3 or 5.4) from CSV files into the CDM tables in the database.

#### Key Features:
- Loads all CSV files for the standardized vocabularies from the specified directory into the corresponding create database. For clarity the database can be created using the executeSQL function from the commondatamodel package. Not minding, we also incorporated it here.

```python
from db_connector import DatabaseHandler

# Initialize the database connection
database_connector = DatabaseHandler(
    db_type="postgresql",
    host="localhost",
    user="postgres",
    password="your_password",
    database="ohdsi_cdm",
    driver_path="path_to_driver"
)

# Connect to the CDM database
db_conn = database_connector.connect_to_db()
# generate the table in the database
database_connector.execute_ddl(cdm_version = "value", cdm_database_schema = "schema name")
```
- Uses the active database connection and CDM-compliant table structure.

#### Example (Python):

```python
from load_csv import CSVLoader

csv_loader = CSVLoader(
    db_connection=db_conn,  # Active database connection
    database_handler=database_connector,  # DatabaseHandler instance
    table_name="your_cdm_table_name"  # CDM table name
)

csv_loader.load_all_csvs("path_to_your_csv_directory")
```

### 3. `main.py`

This is the main entry point of the application. It integrates the database connection and CSV loading functionality specifically for OHDSI's CDM.

#### Usage:

The script connects to the CDM database and loads all relevant CDM data from OHDSI’s standardized vocabularies (versions 5.3 or 5.4).

```bash
python main.py
```

#### Workflow in Main Script:

```python
from db_connector import DatabaseHandler
from load_csv import CSVLoader

# Initialize the database connection
database_connector = DatabaseHandler(
    db_type="postgresql",
    host="localhost",
    user="postgres",
    password="your_password",
    database="ohdsi_cdm",
    driver_path="path_to_driver"
)

# Connect to the CDM database
db_conn = database_connector.connect_to_db()

# Load CSVs if the connection is successful
if db_conn:
    csv_loader = CSVLoader(db_conn, database_connector, "cdm_table_name")
    csv_loader.load_all_csvs("path_to_your_csv_directory")
else:
    print("Database connection failed.")
```

## Environment Variables

To ensure security and flexibility, it is recommended to store database credentials as environment variables rather than hardcoding them into the script.

Here’s an example of how to set environment variables:

```bash
export DB_HOST='your_host'
export DB_NAME='ohdsi_cdm'
export DB_USER='your_username'
export DB_PASSWORD='your_password'
```

Update the script to read these variables using `os.getenv`:

```python
import os
from db_connector import DatabaseHandler

database_connector = DatabaseHandler(
    db_type="postgresql",
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    driver_path="path_to_driver"
)
```

## Credits

This project is designed to work with OHDSI's Common Data Model (CDM) and standardized vocabularies. The tools and processes used here are compatible with OHDSI standards, and the database loader has been tested specifically for PostgreSQL, though it should work with other databases supported by OHDSI.

[![OHDSI](https://www.ohdsi.org/wp-content/uploads/2022/04/OHDSI-Logo.png)](https://ohdsi.org)  
**OHDSI** (Observational Health Data Sciences and Informatics) is a multi-stakeholder, interdisciplinary collaborative that aims to bring out the value of observational health data through large-scale analytics. Learn more about OHDSI and the CDM on the [official OHDSI website](https://ohdsi.org).

[![eHealth Hub Limerick](https://ehealth4cancer.org/wp-content/uploads/2021/12/eHealth4cancer-logo-color.png)](https://ehealth4cancer.org)  
This project was also supported by **eHealth Hub Limerick**, contributing to the development and deployment of health data tools for innovative healthcare solutions. Learn more about eHealth Hub Limerick at [eHealth Hub Limerick's official website](https://ehealth4cancer.org).

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.