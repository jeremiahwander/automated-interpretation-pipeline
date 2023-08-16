#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
# DATE=${1:-$(date +%F)}
DATE="2023-01-02"
# make a randomized config name
CONFIG_PATH=https://kahlquisrefsa.blob.core.windows.net/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml

python3 /home/kahlquis/automated-interpretation-pipeline/reanalysis/generate_workflow_config.py \
  --dataset rgptest \
  --access_level test \
  --driver_image kahlquisaipcr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train/comparison_test/${DATE}" \
  --image_base kahlquisaipcr.azurecr.io/cpg-common/images \
  --reference_base https://kahlquisref.blob.core.windows.net/reference \
  --server_config /home/kahlquis/cpg-deploy/aip/terraform.tfvars.json \
  --deploy_config /home/kahlquis/deploy_config.json \
  --extra_configs /home/kahlquis/automated-interpretation-pipeline/reanalysis/reanalysis_global.toml \
  -o "${CONFIG_PATH}"
  
export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 comparison/comparison_wrapper.py \
  --results https://kahlquisrefsa.blob.core.windows.net/test/reanalysis_train/2023-07-20/ \
  --truth "https://kahlquisrefsa.blob.core.windows.net/test/test-seqr-vars/saved_all_variants_rare_genomes_project_genomes_combined.tsv" \
  --mt https://kahlquisrefsa.blob.core.windows.net/test/annotated_variants.mt \
  --fam_name pedigree_2023-07-21_18:16.fam