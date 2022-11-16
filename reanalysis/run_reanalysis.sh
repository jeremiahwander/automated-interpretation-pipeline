#!/usr/bin/env bash

set -ex

# set the date, or provide a default
DATE=${1:-$(date +%F)}

#     -i hail-az://sevgen002sa/test/reanalysis/986d792a448c66a8a5cfba65434e7d1ce9b1ff_1051-validation.mt \

analysis-runner \
  --dataset severalgenomes \
  --description "AIP run" \
  -o "reanalysis/${DATE}" \
  --access-level test \
  --config reanalysis/reanalysis_global.toml \
  --config reanalysis/reanalysis_cohort.toml \
  reanalysis/interpretation_runner.py \
    -i hail-az://sevgen002sa/test/reanalysis/2022-11-16/prior_to_annotation.vcf.bgz \
    --pedigree hail-az://sevgen002sa/test/reanalysis/pedigree.fam
