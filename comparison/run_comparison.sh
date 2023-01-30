#!/usr/bin/env bash

set -ex

# set the date, or provide a default
PAP_DATE=${1:-$(date +%F)}

# run
analysis-runner \
  --config reanalysis/reanalysis_global.toml \
  --dataset rgp \
  --description "Run Comparison" \
  -o "reanalysis/comparison/${PAP_DATE}" \
  --access-level test \
  comparison/comparison_wrapper.py \
    --results hail-az://raregen001sa/test-analysis/reanalysis_train/2023-01-26/ \
    --seqr hail-az://raregen001sa/test/inputs/rgp/saved_known_gene_for_phenotype_variants_rare_genomes_project_genomes_hmb.tsv \
    --mt hail-az://raregen001sa/test/reanalysis_train/2023-01-26/annotated_variants.mt \
    --fam_name pedigree_2023-01-26_21:56.fam
