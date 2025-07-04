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

## 3. Core packages (excluding arrow for now) -------------------
core_pkgs <- c(
  "rmarkdown",
  "SqlRender",
  "DatabaseConnector",
  "CommonDataModel"
)

install2 <- Sys.which("install2.r")
if (nzchar(install2)) {
  system2(install2, c("--error", sprintf("-l%s", local_lib), core_pkgs))
} else {
  install.packages(core_pkgs, lib = local_lib, dependencies = TRUE)
}

## 4. Try multiple approaches for arrow --------------------------
arrow_installed <- FALSE

# Approach 1: Standard installation
if (!arrow_installed) {
  cat("Trying standard arrow installation...\n")
  tryCatch({
    install.packages("arrow", lib = local_lib, dependencies = TRUE)
    if (requireNamespace("arrow", quietly = TRUE)) {
      arrow_installed <- TRUE
      cat("✅ Standard arrow installation successful\n")
    }
  }, error = function(e) {
    cat("❌ Standard installation failed:", conditionMessage(e), "\n")
  })
}

# Approach 2: From POSIT repo specifically
if (!arrow_installed) {
  cat("Trying arrow from POSIT repo...\n")
  tryCatch({
    install.packages("arrow", lib = local_lib, repos = "https://packagemanager.posit.co/cran/latest")
    if (requireNamespace("arrow", quietly = TRUE)) {
      arrow_installed <- TRUE
      cat("✅ POSIT repo arrow installation successful\n")
    }
  }, error = function(e) {
    cat("❌ POSIT repo installation failed:", conditionMessage(e), "\n")
  })
}

# Approach 3: Binary only
if (!arrow_installed) {
  cat("Trying binary-only arrow installation...\n")
  tryCatch({
    install.packages("arrow", lib = local_lib, type = "binary", dependencies = TRUE)
    if (requireNamespace("arrow", quietly = TRUE)) {
      arrow_installed <- TRUE
      cat("✅ Binary arrow installation successful\n")
    }
  }, error = function(e) {
    cat("❌ Binary installation failed:", conditionMessage(e), "\n")
  })
}

if (!arrow_installed) {
  cat("⚠️  Arrow installation failed with all methods. Consider using system package r-cran-arrow\n")
}

## 5. Sanity check -----------------------------------------------
required <- c("DatabaseConnector", "SqlRender")
missing  <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing))
  stop("Critical packages failed to load: ", paste(missing, collapse = ", "))

cat("✅ All critical packages are present\n")

## 6. Summary -----------------------------------------------------
cat("\nInstalled packages in ", local_lib, ":\n", sep = "")
print(installed.packages(lib.loc = local_lib)[, c("Package", "Version")])

cat("\n🎉 installer.R finished successfully\n")