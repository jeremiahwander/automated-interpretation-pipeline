#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
DATE=${1:-$(date +%F)}
#DATE="2023-01-26"
# make a randomized config name
CONFIG_PATH=hail-az://raregen001sa/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml

python3 reanalysis/generate_workflow_config.py \
  --dataset rgp \
  --access_level test \
  --driver_image azcpg001acr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train/comparison/${DATE}" \
  --image_base azcpg001acr.azurecr.io/cpg-common/images \
  --reference_base hail-az://azcpg001sa/reference \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  -o "${CONFIG_PATH}"
  
export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 comparison/comparison_wrapper.py \
  --results hail-az://raregen001sa/test-analysis/reanalysis_train/2023-01-31/ \
  --truth "hail-az://raregen001sa/test/inputs/rgp/CAGI6_RGP Training Set Key.xlsx" \
  --mt hail-az://raregen001sa/test/reanalysis_train/2023-01-26/annotated_variants.mt \
  --fam_name pedigree_2023-01-31_22:13.fam
