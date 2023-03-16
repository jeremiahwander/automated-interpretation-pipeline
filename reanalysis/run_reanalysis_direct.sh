#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
DATE=${1:-$(date +%F)}
#DATE="2023-02-15"
# make a randomized config name
CONFIG_PATH=hail-az://sevgen002sa/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml

  # --deploy_config ~/sources/cpg/cpg-deploy/azure/deploy-config.prod.json \
  # --server_config ~/sources/cpg/cpg-deploy/aip/terraform.tfvars.json \
python3 reanalysis/generate_workflow_config.py \
  --dataset rgp \
  --access_level test \
  --driver_image azcpg001acr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train_test_cpg/${DATE}" \
  --extra_datasets severalgenomes rgp \
  --image_base azcpg001acr.azurecr.io/cpg-common/images \
  --reference_base hail-az://azcpg001sa/reference \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  -o ${CONFIG_PATH}


#  -i hail-az://raregen001sa/test/inputs/rgp/cpg/3355c9263be6d4b6e13c88b95fb0e3bc1bc99d_1559-broad-rgp.mt \

export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 reanalysis/interpretation_runner.py \
  -i hail-az://raregen001sa/test/reanalysis_train_test_cpg/2023-02-15/annotated_variants.mt \
  --pedigree hail-az://raregen001sa/test/inputs/rgp/cpg/rgp_train_test_cpg.fam \
  --participant_panels hail-az://raregen001sa/test/inputs/rgp/cpg/participant_panels.json \
  --skip_annotation
