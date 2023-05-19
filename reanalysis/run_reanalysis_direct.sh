#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
#DATE=${1:-$(date +%F)}
DATE="2023-05-19"
# make a randomized config name
CONFIG_PATH=hail-az://kahlquisrefsa/test/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml
#CONFIG_PATH=temp.toml


  # --deploy_config ~/sources/cpg/cpg-deploy/azure/deploy-config.prod.json \
  # --server_config ~/sources/cpg/cpg-deploy/aip/terraform.tfvars.json \
python3 reanalysis/generate_workflow_config.py \
  --dataset rgptest \
  --access_level test \
  --driver_image kahlquisaipcr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train/${DATE}" \
  --image_base kahlquisaipcr.azurecr.io/cpg-common/images \
  --reference_base hail-az://kahlquisref/reference \
  --server_config /home/kahlquis/cpg-deploy/aip/terraform.tfvars.json \
  --deploy_config /home/kahlquis/deploy_config.json \
  --extra_configs reanalysis/reanalysis_global.toml reanalysis/reanalysis_cohort.toml \
  -o ${CONFIG_PATH}
  
# export CPG_CONFIG_PATH=${CONFIG_PATH}
# python3 reanalysis/interpretation_runner.py \
#   -i hail-az://kahlquisref/test/inputs/prior_to_annotation.vcf.bgz \
#   --pedigree hail-az://kahlquisref/test/inputs/pedigree.fam

# export CPG_CONFIG_PATH=${CONFIG_PATH}
# python3 reanalysis/interpretation_runner.py \
#   -i hail-az://kahlquisref/test/inputs/single_line_test.vcf.gz \
#   --pedigree hail-az://kahlquisref/test/inputs/single_line_test.ped

# export CPG_CONFIG_PATH=${CONFIG_PATH}
# python3 reanalysis/interpretation_runner.py \
#   -i hail-az://kahlquisref/test/inputs/grch38_WAS_plus_seqdict.vcf.gz \
#   --pedigree hail-az://kahlquisref/test/inputs/grch38_WAS.ped

# export CPG_CONFIG_PATH=${CONFIG_PATH}
# python3 reanalysis/interpretation_runner.py \
#   -i hail-az://kahlquisref/test/inputs/grch38_WAS_male01.vcf.gz \
#   --pedigree hail-az://kahlquisref/test/inputs/grch38_WAS_male.ped

export CPG_CONFIG_PATH=${CONFIG_PATH}
python3 reanalysis/interpretation_runner.py \
  -i hail-az://kahlquisref/reference/RGP_data/RGP_microsoft_output_111422_train.vcf.bgz \
  --pedigree hail-az://kahlquisref/reference_RGP_data/train_pedigree.fam