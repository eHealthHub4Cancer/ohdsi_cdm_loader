#!/usr/bin/env Rscript
# -------------------------------------------------------------
# installer.R – R‑package bootstrap **without** {devtools}
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

cat("Installing rJava with custom configuration...\n")
install.packages("rJava", lib = local_lib, configure.args = "--disable-jri", 
                dependencies = TRUE)

## 3. Core packages (CRAN / R‑Universe) --------------------------
core_pkgs <- c(
  "rmarkdown",
  "SqlRender",
  "arrow",
  "DatabaseConnector",
  "CommonDataModel"
)

install2 <- Sys.which("install2.r")
if (nzchar(install2)) {
  system2(install2, c("--error", sprintf("-l%s", local_lib), core_pkgs))
} else {
  install.packages(core_pkgs, lib = local_lib, dependencies = TRUE)
}

## 4. Sanity check -----------------------------------------------
required <- c("DatabaseConnector", "SqlRender")
missing  <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing))
  stop("Critical packages failed to load: ", paste(missing, collapse = ", "))

cat("✅ All critical packages are present\n")

## 5. Summary -----------------------------------------------------
cat("\nInstalled packages in ", local_lib, ":\n", sep = "")
print(installed.packages(lib.loc = local_lib)[, c("Package", "Version")])
# Ensure arrow works for arm64
if (grepl("arm64", R.version$arch)) {
  cat("\nDetected arm64 architecture. Ensuring 'arrow' compatibility...\n")
  tryCatch({
    install.packages("arrow", type = "source", lib = local_lib)
    cat("\n'arrow' installed successfully for arm64.\n")
  }, error = function(e) {
    cat("\nFailed to install 'arrow' for arm64: ", e$message, "\n")
  })
}
cat("\n🎉 installer.R finished successfully\n")