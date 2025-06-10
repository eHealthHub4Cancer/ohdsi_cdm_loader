local_lib <- '/usr/local/lib/R/site-library'
dir.create(local_lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(local_lib, .libPaths()))
install.packages(c('devtools', 'DatabaseConnector', 'SqlRender', 'arrow'),
                 repos='https://cloud.r-project.org',
                 lib = local_lib)
devtools::install_github('OHDSI/CommonDataModel', lib = local_lib)
devtools::install_github('OHDSI/ETL-Synthea', lib = local_lib)
