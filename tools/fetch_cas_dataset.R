#!/usr/bin/env Rscript
#
# Fetch a single dataset from the CASdatasets R package (Dutang & Charpentier)
# and export it to CSV, without installing/compiling the full package.
#
# Usage:
#   Rscript tools/fetch_cas_dataset.R <dataset_name> <output_csv_path>
#
# Example:
#   Rscript tools/fetch_cas_dataset.R beMTPL97 .tmp/beMTPL97.csv

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript fetch_cas_dataset.R <dataset_name> <output_csv_path>")
}
dataset_name <- args[1]
output_csv <- args[2]

repo_tarball_url <- "http://dutangc.perso.math.cnrs.fr/RRepository/pub/src/contrib/CASdatasets_1.2-1.tar.gz"
cache_dir <- file.path(dirname(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1])))), ".tmp")
if (!dir.exists(cache_dir)) dir.create(cache_dir, recursive = TRUE)
cached_tarball <- file.path(cache_dir, "CASdatasets_1.2-1.tar.gz")

if (!file.exists(cached_tarball)) {
  message("Downloading CASdatasets source tarball (~245MB, one-time)...")
  download.file(repo_tarball_url, cached_tarball, mode = "wb", quiet = FALSE)
}

rda_path_in_tar <- file.path("CASdatasets", "data", paste0(dataset_name, ".rda"))
extract_dir <- tempfile("casdatasets_extract_")
dir.create(extract_dir)
untar(cached_tarball, files = rda_path_in_tar, exdir = extract_dir)

rda_file <- file.path(extract_dir, rda_path_in_tar)
if (!file.exists(rda_file)) {
  stop(sprintf("Dataset '%s' not found in CASdatasets package.", dataset_name))
}

env <- new.env()
load(rda_file, envir = env)
obj_name <- ls(env)[1]
df <- get(obj_name, envir = env)

dir.create(dirname(output_csv), recursive = TRUE, showWarnings = FALSE)
write.csv(df, output_csv, row.names = FALSE)

message(sprintf("Wrote %d rows x %d cols to %s", nrow(df), ncol(df), output_csv))
