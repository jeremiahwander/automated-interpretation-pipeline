#!/usr/bin/env python3


"""
Entrypoint for the interpretation pipeline process, runs the end-to-end
pipeline stages either directly or via Hail Batch(es)
 - Data extraction from PanelApp
 - Filtering and Annotation of variant data
 - Re-headering of resultant VCF

Steps are run only where the specified output does not exist
i.e. the full path to the output file is crucial, and forcing steps to
re-run currently requires the deletion of previous outputs
"""


from typing import Any
import logging
import os
import sys

import click
from cloudpathlib import AnyPath
import hailtop.batch as hb

from cpg_utils.config import get_config
from cpg_utils.git import (
    prepare_git_job,
    get_git_commit_ref_of_current_repository,
    get_organisation_name_from_current_directory,
    get_repo_name_from_current_directory,
)
from cpg_utils.hail_batch import (
    authenticate_cloud_credentials_in_job,
    copy_common_env,
    output_path,
    query_command,
    remote_tmpdir,
)

import annotation
from vep.jobs import vep_jobs, SequencingType


# static paths to write outputs
INPUT_AS_VCF = output_path('prior_to_annotation.vcf.bgz')

# phases of annotation
ANNOTATED_MT = output_path('annotated_variants.mt')

# panelapp query results
PANELAPP_JSON_OUT = output_path('panelapp_137_data.json')

# output of labelling task in Hail
HAIL_VCF_OUT = output_path('hail_categorised.vcf.bgz')

DEFAULT_IMAGE = get_config()['workflow']['driver_image']
assert DEFAULT_IMAGE

# local script references
HAIL_FILTER = os.path.join(os.path.dirname(__file__), 'hail_filter_and_label.py')
HTML_SCRIPT = os.path.join(os.path.dirname(__file__), 'html_builder.py')
QUERY_PANELAPP = os.path.join(os.path.dirname(__file__), 'query_panelapp.py')
RESULTS_SCRIPT = os.path.join(os.path.dirname(__file__), 'validate_categories.py')
MT_TO_VCF_SCRIPT = os.path.join(os.path.dirname(__file__), 'mt_to_vcf.py')


def set_job_resources(
    job: hb.batch.job.Job,
    auth=False,
    git=False,
    prior_job: hb.batch.job.Job | None = None,
    memory: str = 'standard',
):
    """
    applied resources to the job
    :param job:
    :param auth: if true, authenticate gcloud in this container
    :param git: if true, pull this repository into container
    :param prior_job:
    :param memory:
    """
    # apply all settings
    job.cpu(2).image(DEFAULT_IMAGE).memory(memory).storage('20G')

    if prior_job is not None:
        job.depends_on(prior_job)

    if auth:
        authenticate_cloud_credentials_in_job(job)

    if git:
        # copy the relevant scripts into a Driver container instance
        prepare_git_job(
            job=job,
            organisation=get_organisation_name_from_current_directory(),
            repo_name=get_repo_name_from_current_directory(),
            commit=get_git_commit_ref_of_current_repository(),
        )


def mt_to_vcf(batch: hb.Batch, input_file: str, config: dict[str, Any]):
    """
    takes a MT and converts to VCF
    :param batch:
    :param input_file:
    :param config:
    :return:
    """
    mt_to_vcf_job = batch.new_job(name='Convert MT to VCF')
    set_job_resources(mt_to_vcf_job, git=True, auth=True)

    job_cmd = (
        f'PYTHONPATH=$(pwd) python3 {MT_TO_VCF_SCRIPT} '
        f'--input {input_file} '
        f'--output {INPUT_AS_VCF}'
    )

    # if the config has an additional header file, add argument
    vqsr_file = config.get('vqsr_header_file')
    if vqsr_file:
        job_cmd += f' --additional_header {vqsr_file}'

    logging.info(f'Command used to convert MT: {job_cmd}')
    copy_common_env(mt_to_vcf_job)
    mt_to_vcf_job.command(job_cmd)
    return mt_to_vcf_job


def annotate_vcf(
    input_vcf: str,
    batch: hb.Batch,
    vep_temp: str,
    vep_out: str,
    seq_type: SequencingType | None = SequencingType.GENOME,
) -> list[hb.batch.job.Job]:
    """
    takes the VCF path, schedules all annotation jobs, creates MT with VEP annos.

    should this be separated out into a script and run end2end, or should we
    continue in this same runtime? These jobs are scheduled into this batch with
    appropriate dependencies, so keeping this structure seems valid

    :param input_vcf:
    :param batch:
    :param vep_temp:
    :param vep_out:
    :param seq_type:
    :return:
    """

    # generate the jobs which run VEP & collect the results
    return vep_jobs(
        b=batch,
        vcf_path=AnyPath(input_vcf),
        hail_billing_project=get_config()['hail']['billing_project'],
        hail_bucket=AnyPath(remote_tmpdir()),
        tmp_bucket=AnyPath(vep_temp),
        out_path=AnyPath(vep_out),
        overwrite=False,  # don't re-run annotation on completed chunks
        sequencing_type=seq_type,
        job_attrs={},
    )


def annotated_mt_from_ht_and_vcf(
    input_vcf: str,
    batch: hb.Batch,
    vep_ht: str,
    job_attrs: dict | None = None,
) -> hb.batch.job.Job:
    """
    apply the HT of annotations to the VCF, save as MT
    :return:
    """
    apply_anno_job = batch.new_job('HT + VCF = MT', job_attrs)

    copy_common_env(apply_anno_job)
    apply_anno_job.image(DEFAULT_IMAGE)

    cmd = query_command(
        annotation,
        annotation.apply_annotations.__name__,
        input_vcf,
        vep_ht,
        ANNOTATED_MT,
        setup_gcp=True,
        hail_billing_project=get_config()['hail']['billing_project'],
        hail_bucket=str(remote_tmpdir()),
        default_reference='GRCh38',
        packages=['seqr-loader==1.2.5'],
    )
    apply_anno_job.command(cmd)
    return apply_anno_job


def handle_panelapp_job(
    batch: hb.Batch,
    gene_list: str | None = None,
    prev_version: str | None = None,
    prior_job: hb.batch.job.Job | None = None,
) -> hb.batch.job.Job:
    """

    :param batch:
    :param gene_list:
    :param prev_version:
    :param prior_job:
    """
    panelapp_job = batch.new_job(name='query panelapp')
    set_job_resources(panelapp_job, auth=True, git=True, prior_job=prior_job)
    panelapp_command = (
        f'python3 {QUERY_PANELAPP} --panel_id 137 --out_path {PANELAPP_JSON_OUT} '
    )
    if gene_list is not None:
        panelapp_command += f'--gene_list {gene_list} '
    elif prev_version is not None:
        panelapp_command += f'--previous_version {prev_version} '

    if prior_job is not None:
        panelapp_job.depends_on(prior_job)

    logging.info(f'PanelApp Command: {panelapp_command}')
    panelapp_job.command(panelapp_command)
    return panelapp_job


def handle_hail_filtering(
    batch: hb.Batch,
    config: str,
    plink_file: str,
    prior_job: hb.batch.job.Job | None = None,
) -> hb.batch.job.BashJob:
    """
    hail-query backend version of the filtering implementation
    use the init query service instead of running inside dataproc

    :param batch:
    :param config:
    :param plink_file:
    :param prior_job:
    :return:
    """

    labelling_job = batch.new_job(name='hail filtering')
    set_job_resources(
        labelling_job, auth=True, git=True, prior_job=prior_job, memory='16Gi'
    )
    labelling_command = (
        f'pip install . && '
        f'python3 {HAIL_FILTER} '
        f'--mt {ANNOTATED_MT} '
        f'--panelapp {PANELAPP_JSON_OUT} '
        f'--config_path {config} '
        f'--plink {plink_file}'
    )

    logging.info(f'Labelling Command: {labelling_command}')
    labelling_job.command(labelling_command)
    copy_common_env(labelling_job)
    return labelling_job


def handle_results_job(
    batch: hb.Batch,
    config: str,
    labelled_vcf: str,
    pedigree: str,
    output_dict: dict[str, dict[str, str]],
    prior_job: hb.batch.job.Job | None = None,
) -> hb.batch.job.Job:
    """
    one container to run the MOI checks, and the presentation

    :param batch:
    :param config:
    :param labelled_vcf:
    :param pedigree:
    :param output_dict: paths to the
    :param prior_job:
    :return:
    """

    results_job = batch.new_job(name='finalise_results')
    set_job_resources(results_job, auth=True, git=True, prior_job=prior_job)
    results_command = (
        'pip install . && '
        f'python3 {RESULTS_SCRIPT} '
        f'--config_path {config} '
        f'--labelled_vcf {labelled_vcf} '
        f'--panelapp {PANELAPP_JSON_OUT} '
        f'--pedigree {pedigree} '
        f'--out_json {output_dict["results"]} && '
        f'python3 {HTML_SCRIPT} '
        f'--results {output_dict["results"]} '
        f'--config_path {config} '
        f'--panelapp {PANELAPP_JSON_OUT} '
        f'--pedigree {pedigree} '
        f'--out_path {output_dict["web_html"]}'
    )
    logging.info(f'Results command: {results_command}')
    results_job.command(results_command)
    return results_job


@click.command()
@click.option(
    '--input_path', help='variant matrix table or VCF to analyse', required=True
)
@click.option('--config_json', help='JSON dict of runtime settings', required=True)
@click.option('--plink_file', help='Plink file path for the cohort', required=True)
def main(input_path: str, config_json: str, plink_file: str):
    """
    main method, which runs the full reanalysis process

    :param input_path: annotated input matrix table or VCF
    :param config_json:
    :param plink_file:
    """

    if not AnyPath(input_path).exists():
        raise Exception(
            f'The provided path "{input_path}" does not exist or is inaccessible'
        )

    logging.info('Starting the reanalysis batch')
    service_backend = hb.ServiceBackend(
        billing_project=get_config()['hail']['billing_project'],
        remote_tmpdir=remote_tmpdir(),
    )
    batch = hb.Batch(
        name='AIP batch',
        backend=service_backend,
        cancel_after_n_failures=1,
        default_timeout=6000,
        default_memory='highmem',
    )

    # read the ped file into the Batch
    pedigree_in_batch = batch.read_input(plink_file)

    # set a first job in this batch
    prior_job = None
    _prior_job = handle_hail_filtering(
        batch=batch,
        config=config_json,
        prior_job=prior_job,
        plink_file=pedigree_in_batch,
    )

    batch.run(wait=False)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stderr,
    )
    main()  # pylint: disable=E1120
