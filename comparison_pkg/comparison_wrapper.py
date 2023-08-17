#!/usr/bin/env python3


"""
Entrypoint for the comparison process
"""


import logging
import os
import sys

from argparse import ArgumentParser

import hailtop.batch as hb

from cpg_utils.git import (
    prepare_git_job,
    get_git_commit_ref_of_current_repository,
    get_organisation_name_from_current_directory,
    get_repo_name_from_current_directory,
    get_git_root_relative_path_from_absolute
)
from cpg_utils.hail_batch import (
    authenticate_cloud_credentials_in_job,
    copy_common_env,
    image_path,
    remote_tmpdir,
    output_path,
)
from cpg_utils.config import get_config

# Namespacing gets weird here because both the package and the module share the same name. When running via shell script
# this will import the module, thus it follows a different pattern from reanalysis/interpretation_runner.py.
import comparison
import importlib
importlib.reload(comparison)


def main(results_folder: str, truth: str, mt: str, fam_name: str):
    """
    main method, which runs the AIP comparison
    :param results_folder:
    :param truth:
    :param mt:
    :return:
    """

    # set up a batch
    service_backend = hb.ServiceBackend(
        billing_project=get_config()['hail']['billing_project'],
        remote_tmpdir=remote_tmpdir(),
    )
    batch = hb.Batch(name='run AIP comparison', backend=service_backend)

    # create a new job
    comp_job = batch.new_job(name='Run Comparison')

    # set reasonable job resources
    comp_job.cpu(4).image(image_path('cpg_aip')).memory('standard').storage('50G')

    # # run gcloud authentication
    # authenticate_cloud_credentials_in_job(comp_job)

    # # copy in Env Variables from current config
    copy_common_env(comp_job)

    # need to localise the VCF + index
    run_vcf = os.path.join(results_folder, 'hail_categorised.vcf.bgz')
    vcf_in_batch = batch.read_input_group(
        **{'vcf.bgz': run_vcf, 'vcf.bgz.tbi': run_vcf + '.tbi'}
    )
    ped_in_batch = batch.read_input(os.path.join(results_folder, fam_name))

    script_path = get_git_root_relative_path_from_absolute(comparison.__file__)
    print(os.getcwd())
    print(sys.path)
    output = output_path("comparison_result")
    results_command = (
        f'python3 comparison/comparison.py '
        f'--results_folder {results_folder} '
        f'--pedigree {ped_in_batch} '
        f'--seqr "{truth}" '
        f'--vcf {vcf_in_batch["vcf.bgz"]} '
        f'--mt {mt} '
        f'--output {output} '
    )
    print(results_command)
    logging.info(f'Results command: {results_command}')
    comp_job.command(results_command)

    batch.run(wait=False)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stderr,
    )
    parser = ArgumentParser()
    parser.add_argument('--results', help='results folder', required=True)
    parser.add_argument('--truth', help='Flagged Truth variants (seqr export or xlsx)', required=True)
    parser.add_argument('--mt', help='Hail MT of annotated variants', required=True)
    parser.add_argument('--fam_name', help='pedigree filename within results folder (defaults to "latest_pedigree.fam")', default="latest_pedigree.fam")
    args = parser.parse_args()
    main(results_folder=args.results, truth=args.truth, mt=args.mt, fam_name=args.fam_name)
