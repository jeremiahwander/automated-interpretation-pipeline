#!/usr/bin/env bash

set -ex

# set the date, or provide a default
PAP_DATE=${1:-"2011-11-11"}

analysis-runner \
  --dataset severalgenomes \
  --description "AIP runtime test" \
  -o "reanalysis/${PAP_DATE}" \
  --access-level standard \
  --env CPG_CONFIG_PATH="hail-az://sevgen002sa/cpg-severalgenomes-main/cpg-config.toml" \
  reanalysis/interpretation_runner.py \
    --config_json hail-az://sevgen002sa/cpg-severalgenomes-main/reanalysis/reanalysis_conf.json \
    --input_path hail-az://sevgen002sa/cpg-severalgenomes-main/reanalysis/986d792a448c66a8a5cfba65434e7d1ce9b1ff_1051-validation.mt \
    --panel_genes hail-az://sevgen002sa/cpg-severalgenomes-main/reanalysis/pre_panelapp_mendeliome.json \
    --plink_file hail-az://sevgen002sa/cpg-severalgenomes-main/reanalysis/severalgenomes-plink.fam \
    --skip_annotation
