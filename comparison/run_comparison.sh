#!/usr/bin/env bash

set -ex

# set the date, or provide a default
DATE=${1:-$(date +%F)}

# run
analysis-runner \
  --config reanalysis/reanalysis_global.toml \
  --dataset rgp \
  --image azcpg001acr.azurecr.io/cpg-common/images/cpg_aip \
  --description "Run Comparison" \
  -o "reanalysis/comparison/${DATE}" \
  --access-level test \
  comparison/comparison_wrapper.py \
    --results hail-az://raregen001sa/test-analysis/reanalysis_train/2023-01-31/ \
    --truth "hail-az://raregen001sa/test/inputs/rgp/CAGI6_RGP Training Set Key.xlsx" \
    --mt hail-az://raregen001sa/test/reanalysis_train/2023-01-26/annotated_variants.mt \
    --fam_name pedigree_2023-01-31_22:13.fam
