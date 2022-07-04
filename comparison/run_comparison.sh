#!/usr/bin/env bash

set -ex

analysis-runner \
    --dataset acute-care \
    --description "run AIP comparison MVP" \
    -o "reanalysis/comparison" \
    --access-level test \
    comparison/comparison_wrapper.py \
        --results gs://cpg-acute-care-test/reanalysis/2022-07-01/summary_results.json \
        --seqr gs://cpg-acute-care-test/reanalysis/comparison/seqr_acute_care_tags.tsv \
        --mt gs://cpg-acute-care-main/mt/e51f4fb948f27a4130f4a56b32fd1ca8e7c0ad_867-acute-care.mt \
        --vcf gs://cpg-acute-care-test/reanalysis/2022-07-01/hail_categorised.vcf.bgz \
        --config gs://cpg-acute-care-test/reanalysis/reanalysis_conf.json \
        --panel gs://cpg-acute-care-test/reanalysis/2022-07-01/panelapp_137_data.json \
        --ped gs://cpg-acute-care-test/reanalysis/2022-06-27/pedigree.fam \
        --output gs://cpg-acute-care-test/reanalysis
