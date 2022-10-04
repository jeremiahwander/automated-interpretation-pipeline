#!/usr/bin/env bash

set -ex

export CPG_DEPLOY_CONFIG
analysis-runner \
  --dataset severalgenomes \
  --description "MS CPG infra test" \
  --access-level standard \
  --output-dir "miah_test" \
  --env CPG_CONFIG_PATH="hail-az://sevgen002sa/cpg-severalgenomes-main/cpg-config.toml" \
  reanalysis/test_cpg_infra.py \
    --blob hail-az://sevgen002sa/cpg-severalgenomes-test/hello.txt