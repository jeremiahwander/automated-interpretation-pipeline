#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
DATE=${1:-$(date +%F)}
#DATE="2023-02-15"
# make a randomized config name
CONFIG_PATH=hail-az://kaileighdemo1sa/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml

  # --deploy_config ~/sources/cpg/cpg-deploy/azure/deploy-config.prod.json \
  # --server_config ~/sources/cpg/cpg-deploy/aip/terraform.tfvars.json \
python3 reanalysis/generate_workflow_config.py \
  --dataset rgptest \
  --access_level test \
  --driver_image kaileighacr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train/${DATE}" \
  --image_base kaileighacr.azurecr.io/cpg-common/images \
  --reference_base hail-az://kaileighref/reference \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  --server_config /home/azureuser/cpg-deploy/aip/terraform.tfvars.json \
  --deploy_config /home/azureuser/deploy_config.json \
  -o ${CONFIG_PATH}


#  -i hail-az://raregen001sa/test/inputs/rgp/cpg/3355c9263be6d4b6e13c88b95fb0e3bc1bc99d_1559-broad-rgp.mt \

export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 reanalysis/interpretation_runner.py \
  -i hail-az://kaileighdemo1sa/test/inputs/prior_to_annotation.vcf.bgz \
  --pedigree hail-az://kaileighdemo1sa/test/inputs/pedigree.fam
