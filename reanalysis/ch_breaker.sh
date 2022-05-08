#!/usr/bin/env bash

set -ex

# run
analysis-runner \
  --dataset acute-care \
  --description "expose comphet failure" \
  -o reanalysis/comp_het_test \
  --access-level test \
  python3 reanalysis/comphet_collect_fail.py \
    --mt_input gs://cpg-acute-care-test/reanalysis/2021-09-03/hail_categorised.vcf.bgz.mt
