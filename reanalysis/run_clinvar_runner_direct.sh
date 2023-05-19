#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
# DATE=${1:-$(date +%F)}
DATE="2023-05-19"
# make a randomized config name
CONFIG_PATH=hail-az://kahlquisrefsa/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml

  # --deploy_config ~/sources/cpg/cpg-deploy/azure/deploy-config.prod.json \
  # --server_config ~/sources/cpg/cpg-deploy/aip/terraform.tfvars.json \
python3 reanalysis/generate_workflow_config.py \
  --dataset rgptest \
  --access_level test \
  --driver_image kahlquisaipacr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_test/${DATE}" \
  --image_base kahlquisaipacr.azurecr.io/cpg-common/images \
  --reference_base hail-az://kahlquisref/reference \
  --server_config /home/kahlquis/cpg-deploy/aip/terraform.tfvars.json \
  --deploy_config /home/kahlquis/deploy_config.json \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  -o ${CONFIG_PATH}


export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 reanalysis/clinvar_runner.py