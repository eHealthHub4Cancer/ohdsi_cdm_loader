# OHDSI CDM Loader

This repository provides a small Python package for loading OHDSI Common Data Model (CDM) vocabularies and Synthea data into a relational database.  It uses `rpy2` to call R packages from Python so that existing OHDSI tools can be reused from within Python workflows.

## Repository Structure

```
ohdsicdm_loader/
├── db_connector.py  - Database connection helpers using R DatabaseConnector
├── load_csv.py      - Bulk load utilities for CSV files
├── __init__.py
main.py              - Example script showing how to run the loader
requirements.txt     - Python dependencies
setup.py             - Package configuration
```

### `db_connector.py`
Defines `DatabaseHandler` which opens a connection to the database via R's `DatabaseConnector`.  It can execute DDL scripts, create Synthea tables, and run post‑load routines such as building indexes or loading events.

### `load_csv.py`
Contains `CSVLoader` for reading CSV or tab‑delimited files with pandas and inserting the rows in batches using `pg_bulk_loader`.

### `main.py`
Sample entry point that reads settings from environment variables, connects to the database and loads the vocabularies and Synthea data.

## Installation

1. Install the Python requirements:

```bash
pip install -r requirements.txt
```

2. Install the necessary R packages (via R or RStudio):

```r
install.packages("DatabaseConnector")
install.packages("SqlRender")
# For CDM DDL helpers
devtools::install_github("OHDSI/CommonDataModel")
# For Synthea ETL helpers
devtools::install_github("OHDSI/ETL-Synthea")
```

## Configuration

`main.py` relies on environment variables.  These can be stored in a `.env` file:

```bash
DB_TYPE=postgresql
DB_SERVER=localhost
DB_PORT=5432
DB_NAME=ohdsi_cdm
DB_USER=postgres
DB_PASSWORD=secret
DRIVER_PATH=/path/to/jdbc_driver
DB_SCHEMA=cdm_schema
CSV_PATH=/path/to/cdm_csv
CDM_VERSION=5.4
SYNTHEA_VERSION=3.0
SYNTHEA_SCHEMA=synthea_schema
SYNTHEA_CSV=/path/to/synthea_csv
```

## Usage

Once configured, run

```bash
python main.py
```

to connect to the database, load the CSV files and execute the additional ETL steps.

## Next Steps

- Inspect `db_connector.py` and `load_csv.py` to see how Python and R work together.
- Tune the batch size and pool settings in `CSVLoader` for your database environment.
- Review the [OHDSI CDM documentation](https://ohdsi.github.io/CommonDataModel/) for schema details.

## Credits

This project is part of the OHDSI community tools and was developed with support from the eHealth Hub Limerick.

## License

MIT
