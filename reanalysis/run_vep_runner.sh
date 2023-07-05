#!/usr/bin/env bash

set -ex

# Make sure to export CPG_DEPLOY_CONFIG first?

# set the date, or provide a default
DATE=${1:-$(date +%F)}
#DATE="2023-05-02"
# make a randomized config name
CONFIG_PATH=https://raregen001sa.blob.core.windows.net/test-tmp/config-$(LC_ALL=C tr -dc A-Za-z0-9 </dev/urandom | head -c 8).toml
#CONFIG_PATH=temp.toml


  # --deploy_config ~/sources/cpg/cpg-deploy/azure/deploy-config.prod.json \
  # --server_config ~/sources/cpg/cpg-deploy/aip/terraform.tfvars.json \
python3 reanalysis/generate_workflow_config.py \
  --dataset rgp \
  --access_level test \
  --driver_image azcpg001acr.azurecr.io/cpg-common/images/cpg_aip:latest \
  --output_prefix "reanalysis_train/${DATE}" \
  --image_base azcpg001acr.azurecr.io/cpg-common/images \
  --reference_base https://azcpg001sa.blob.core.windows.net/reference \
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

# export CPG_CONFIG_PATH=${CONFIG_PATH}
# python3 reanalysis/interpretation_runner.py \
#   -i https://kahlquisref.blob.core.windows.net/reference/RGP_data/RGP_microsoft_output_111422_train_reheader.vcf.bgz\
#   --pedigree https://kahlquisref.blob.core.windows.net/reference/RGP_data/train_pedigree.fam

export CPG_CONFIG_PATH=${CONFIG_PATH}

python3 reanalysis/vep_runner.py \
  -i "https://raregen001sa.blob.core.windows.net/test/inputs/both_out.vcf.gz" \
  --pedigree https://raregen001sa.blob.core.windows.net/test/inputs/pedigree.fam

# fn_prefix="output_vcf_broken_tiny_179"
# root="/mnt/data/${fn_prefix}"
# for n in {0..21}
# do
#   startline=3432
#   endline=$((startline + n - 1))
#   sed "${startline},${endline}d" "${root}.vcf" | gzip > "${root}_pre${n}.vcf.gz"
#   azcopy cp "${root}_pre${n}.vcf.gz" "https://raregen001sa.blob.core.windows.net/test/inputs/${fn_prefix}_pre${n}.vcf.gz"
#   python3 reanalysis/vep_runner.py \
#     -i "https://raregen001sa.blob.core.windows.net/test/inputs/${fn_prefix}_pre${n}.vcf.gz" \
#     --pedigree https://raregen001sa.blob.core.windows.net/test/inputs/pedigree.fam
# done

# fn_prefix="output_vcf_broken_tiny"
# root="/mnt/data/${fn_prefix}"
# in_startline=3432
# in_endline=$((in_startline + 78 - 1))
# for n in {81..90}
# do
#   out_endline=3555
#   out_startline=$((out_endline - n + 1))
#   sed "${in_startline},${in_endline}d" "${root}.vcf" | sed "${out_startline},${out_endline}d" | gzip > "${root}_78_${n}.vcf.gz"
#   azcopy cp "${root}_${n}.vcf.gz" "https://raregen001sa.blob.core.windows.net/test/inputs/${fn_prefix}_78_${n}.vcf.gz"
#   python3 reanalysis/vep_runner.py \
#     -i "https://raregen001sa.blob.core.windows.net/test/inputs/${fn_prefix}_78_${n}.vcf.gz" \
#     --pedigree https://raregen001sa.blob.core.windows.net/test/inputs/pedigree.fam
# done