#!/usr/bin/env bash

set -ex

# run
analysis-runner \
  --dataset acute-care \
  --description "run comp het mini test process" \
  -o reanalysis/comp_het_test \
  --access-level test \
  reanalysis/isolated_runner.py \
    --matrix_path gs://cpg-acute-care-test/leo-oom-debug/gene_id.mt
