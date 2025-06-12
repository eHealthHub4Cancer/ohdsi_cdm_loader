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

2. Install the necessary R packages (via R or RStudio).  The included
   `install_r_packages.R` script installs everything you need:

```r
source("install_r_packages.R")
```

The key packages are:

- **DatabaseConnector** and **SqlRender** – core OHDSI database utilities.
- **arrow** – for efficient data handling.
- **devtools** – used to install GitHub packages.
- **CommonDataModel** and **ETL-Synthea** from GitHub for DDL helpers and
  Synthea ETL routines.

## Configuration

`main.py` relies on environment variables.  These can be stored in a `.env` file
(a sample `.env.example` is provided):

```
DB_TYPE=postgresql
DB_SERVER=localhost
DB_PORT=5119
DB_NAME=aml_report
DB_USER=postgres
DB_PASSWORD=secret
# Host paths (Windows)
HOST_DRIVER_PATH=C:/Users/23434813/Desktop/AML_data/ohdsi
HOST_CSV_PATH=C:/Users/23434813/Desktop/latest_vocabularies/vocabulary_download_v5_2
HOST_SYNTHEA_PATH=/path/to/synthea
# Container paths
DRIVER_PATH=/app/drivers
CSV_PATH=/app/vocabulary
SYNTHEA_CSV=/app/synthea
DB_SCHEMA=public
CDM_VERSION=5.4
SYNTHEA_VERSION=3.0
SYNTHEA_SCHEMA=synthea_schema
```

## Usage

Once configured, run

```bash
python main.py
```

to connect to the database, create the CDM tables, load the CSV files and execute the additional ETL steps.

### Docker

The repository also contains a `docker-compose.yml` for running the loader and a
Postgres database in containers.

1. Install Docker (for Windows/macOS you can download **Docker Desktop** from
   [docker.com](https://www.docker.com/products/docker-desktop)).
2. Ensure the environment variables described above are available in a `.env`
   file.
3. Start the services with `python launch.py`:

```bash
python launch.py
```

This convenience script runs `docker compose up --build` and, once the
containers are running, automatically opens your default web browser to a
`status.html` page showing a short success message.

If you prefer to run Compose manually simply execute `docker compose up --build`
instead.

## Next Steps

- Inspect `db_connector.py` and `load_csv.py` to see how Python and R work together.
- Tune the batch size and pool settings in `CSVLoader` for your database environment.
- Review the [OHDSI CDM documentation](https://ohdsi.github.io/CommonDataModel/) for schema details.

## Credits

This project is part of the OHDSI community tools and was developed with support from the eHealth Hub Limerick.

## Contributing

Contributions are very welcome! Feel free to open issues or pull requests if you have ideas for improvements or run into problems. The goal is to keep the loader simple and useful for anyone working with the OHDSI CDM.

## License

MIT
