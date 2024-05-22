#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
#DATE=${1:-$(date +%F)}
DATE="2024-04-01"
# make a randomized config name
CONFIG_PATH=https://kahlquisrefsa.blob.core.windows.net/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml
#CONFIG_PATH=temp.toml

python3 reanalysis/generate_workflow_config.py \
  --dataset rgptest \
  --access_level test \
  --driver_image kahlquisaipcr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train/${DATE}" \
  --image_base kahlquisaipcr.azurecr.io/cpg-common/images \
  --reference_base https://kahlquisref.blob.core.windows.net/reference \
  --server_config /home/kahlquis/cpg-deploy/aip/terraform.tfvars.json \
  --deploy_config /home/kahlquis/deploy_config.json \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  -o ${CONFIG_PATH}
  

export CPG_CONFIG_PATH=${CONFIG_PATH}
#echo $CPG_CONFIG_PATH
# python3 reanalysis/interpretation_runner.py \
#   -i https://kahlquisref.blob.core.windows.net/reference/RGP_data/2023_October_RGP_version.vcf.bgz\
#   -sv https://kahlquisref.blob.core.windows.net/reference/RGP_data/sv_mt.mt/\
#   --pedigree https://kahlquisref.blob.core.windows.net/reference/RGP_data/both_train_holdout_pedigree.fam\
#   --participant_panels https://kahlquisref.blob.core.windows.net/reference/RGP_data/both_train_holdout_hpo.json

  python3 reanalysis/interpretation_runner.py \
  -i https://kahlquisref.blob.core.windows.net/reference/RGP_data/2023_October_RGP_version.vcf.bgz\
  --pedigree https://kahlquisref.blob.core.windows.net/reference/RGP_data/both_train_holdout_pedigree.fam\

