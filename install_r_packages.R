#!/usr/bin/env Rscript
# -------------------------------------------------------------
# installer.R – R-package bootstrap using {devtools}
# -------------------------------------------------------------
options(error = function() {
  cat("❌ installer.R halted with an error – aborting\n")
  quit(status = 1)
})

## 1. Library path ------------------------------------------------
local_lib <- "/usr/local/lib/R/site-library"
dir.create(local_lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(local_lib, .libPaths()))

## 2. Repositories ------------------------------------------------
repos <- c(
  OHDSI = "https://ohdsi.r-universe.dev",
  POSIT = "https://packagemanager.posit.co/cran/latest",
  CRAN  = "https://cloud.r-project.org"
)
options(
  repos = repos,
  install.packages.compile.from.source = "ifneeded"  # binary first, else source
)

## 3. Core CRAN / R-universe packages ----------------------------
cran_pkgs <- c(
  "DatabaseConnector",
  "SqlRender",
  "arrow",
  "devtools"
)
install2 <- Sys.which("install2.r")
if (nzchar(install2)) {
  system2(install2, c("--error", sprintf("-l%s", local_lib), cran_pkgs))
} else {
  install.packages(cran_pkgs, lib = local_lib, dependencies = TRUE)
}

## 4. GitHub-only packages via devtools --------------------------
github_repos <- c(
  "OHDSI/CommonDataModel",
  "OHDSI/ETL-Synthea"
)
if (!requireNamespace("devtools", quietly = TRUE))
  install.packages("devtools", lib = local_lib)

for (repo in github_repos) {
  devtools::install_github(
    repo,
    lib          = local_lib,
    dependencies = TRUE,
    upgrade      = "never",
    quiet        = TRUE
  )
}

## 5. Sanity check ----------------------------------------------
required <- c("DatabaseConnector", "SqlRender")
missing  <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing))
  stop("Critical packages failed to load: ", paste(missing, collapse = ", "))

cat("✅ All critical packages are present\n")

## 6. Summary ----------------------------------------------------
cat("\nInstalled packages in ", local_lib, ":\n", sep = "")
print(installed.packages(lib.loc = local_lib)[, c("Package", "Version")])

## 7. Extra manual installs (if ever needed) ---------------------
# install.packages("someExtraPkg", lib = local_lib)
# devtools::install_github("user/anotherPkg", lib = local_lib)

cat("\n🎉 installer.R finished successfully\n")
