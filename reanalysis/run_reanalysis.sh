#!/usr/bin/env bash

set -ex

# set the date, or provide a default
PAP_DATE=${1:-"2011-11-11"}

analysis-runner \
  --dataset severalgenomes \
  --description "AIP runtime test" \
  -o "reanalysis/${PAP_DATE}" \
  --access-level standard \
  --env CPG_CONFIG_PATH="hail-az://sevgen002/cpg-severalgenomes-main/cpg-config.toml" \
  reanalysis/interpretation_runner.py \
    --config_json reanalysis/reanalysis_conf.json \
    --input_path reanalysis/2011-11-11/prior_to_annotation.vcf.bgz \
    --panel_genes reanalysis/pre_panelapp_mendeliome.json \
    --plink_file reanalysis/severalgenomes-plink.fam
