#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
#DATE=${1:-$(date +%F)}
DATE="2023-07-04"
# make a randomized config name
CONFIG_PATH=https://raregen001sa.blob.core.windows.net/test-tmp/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml

  # --deploy_config ~/sources/cpg/cpg-deploy/azure/deploy-config.prod.json \
  # --server_config ~/sources/cpg/cpg-deploy/aip/terraform.tfvars.json \
python3 reanalysis/generate_workflow_config.py \
  --dataset rgp \
  --access_level test \
  --driver_image azcpg001acr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis/${DATE}" \
  --extra_datasets severalgenomes \
  --image_base azcpg001acr.azurecr.io/cpg-common/images \
  --reference_base https://azcpg001sa.blob.core.windows.net/reference \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  -o ${CONFIG_PATH}

export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 reanalysis/interpretation_runner.py \
  -i https://raregen001sa.blob.core.windows.net/test/inputs/RGP_clean.vcf.bgz \
  --pedigree https://raregen001sa.blob.core.windows.net/test/inputs/pedigree.fam
