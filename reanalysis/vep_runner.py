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

# pylint: disable=too-many-branches


import logging
import sys
from argparse import ArgumentParser
from datetime import datetime

from hailtop.batch.job import BashJob, Job

from cpg_utils import to_path
from cpg_utils.config import get_config
from cpg_utils.hail_batch import (
    authenticate_cloud_credentials_in_job,
    copy_common_env,
    output_path,
    query_command,
)
from cpg_utils.git import get_git_root_relative_path_from_absolute
from cpg_utils.hail_batch import (
    fasta_res_group,
    image_path,
    reference_path,
    command,
    authenticate_cloud_credentials_in_job,
    query_command,
)
from cpg_workflows.resources import STANDARD
from cpg_workflows.batch import get_batch
from reanalysis.vep_jobs import vep_one
from reanalysis.sites_only import add_make_sitesonly_job

from reanalysis import (
    hail_filter_and_label,
    html_builder,
    metamist_registration,
    mt_to_vcf,
    query_panelapp,
    validate_categories,
    seqr_loader,
)
from reanalysis.utils import FileTypes, identify_file_type

# region: CONSTANTS
# exact time that this run occurred
EXECUTION_TIME = f'{datetime.now():%Y-%m-%d_%H:%M}'

# static paths to write outputs
ANNOTATED_MT = output_path('annotated_variants.mt')
HAIL_VCF_OUT = output_path('hail_categorised.vcf.bgz', 'analysis')
INPUT_AS_VCF = output_path('prior_to_annotation.vcf.bgz')
PANELAPP_JSON_OUT = output_path('panelapp_data.json', 'analysis')


# endregion


def set_job_resources(
    job: Job,
    prior_job: Job | None = None,
    memory: str = 'standard',
    storage: str = '20Gi',
):
    """
    apply resources to the job

    Args:
        job (Job): the job to set resources on
        prior_job (Job): the job to depend on (or None)
        memory (str): lowmem/standard/highmem
        storage (str): storage setting to use
    """
    # apply all settings to this job
    job.cpu(2).image(get_config()['workflow']['driver_image']).memory(memory).storage(
        storage
    )

    # copy the env variables into the container; specifically CPG_CONFIG_PATH
    copy_common_env(job)

    if prior_job is not None:
        if isinstance(prior_job, list):
            job.depends_on(*prior_job)
        else:
            job.depends_on(prior_job)

    authenticate_cloud_credentials_in_job(job)


def setup_mt_to_vcf(input_file: str) -> Job:
    """
    set up a job MatrixTable conversion to VCF, prior to annotation

    Args:
        input_file (str): path to the MatrixTable

    Returns:
        the new job, available for dependency setting
    """

    job = get_batch().new_job(name='Convert MT to VCF')
    set_job_resources(job)

    script_path = get_git_root_relative_path_from_absolute(mt_to_vcf.__file__)
    cmd = f'python3 {script_path} --input {input_file} --output {INPUT_AS_VCF}'

    logging.info(f'Command used to convert MT: {cmd}')
    job.command(cmd)
    return job


def handle_panelapp_job(
    participant_panels: str | None = None, prior_job: Job | None = None
) -> Job:
    """
    creates and runs the panelapp query job

    Args:
        participant_panels (str):
        prior_job ():

    Returns:
        the Job, which other parts of the workflow may become dependent on
    """

    panelapp_job = get_batch().new_job(name='query panelapp')
    set_job_resources(panelapp_job, prior_job=prior_job)
    copy_common_env(panelapp_job)

    script_path = get_git_root_relative_path_from_absolute(query_panelapp.__file__)
    query_cmd = f'python3 {script_path} --out_path {PANELAPP_JSON_OUT} '

    if participant_panels is not None:
        query_cmd += f'--panels {participant_panels} '

    logging.info(f'PanelApp Command: {query_cmd}')
    panelapp_job.command(query_cmd)
    return panelapp_job


def handle_hail_filtering(plink_file: str, prior_job: Job | None = None) -> BashJob:
    """
    hail-query backend version of the filtering implementation
    use the init query service instead of running inside dataproc

    Args:
        plink_file (str): path to a pedigree
        prior_job ():

    Returns:
        the Batch job running the hail filtering process
    """

    labelling_job = get_batch().new_job(name='hail filtering')
    set_job_resources(labelling_job, prior_job=prior_job, memory='32Gi')
    script_path = get_git_root_relative_path_from_absolute(hail_filter_and_label.__file__)
    labelling_command = (
        f'python3 {script_path} '
        f'--mt {ANNOTATED_MT} '
        f'--panelapp {PANELAPP_JSON_OUT} '
        f'--plink {plink_file} '
    )

    logging.info(f'Labelling Command: {labelling_command}')
    labelling_job.command(labelling_command)
    return labelling_job


def handle_results_job(
    labelled_vcf: str,
    pedigree: str,
    input_path: str,
    output: str,
    prior_job: Job | None = None,
    participant_panels: str | None = None,
):
    """
    one container to run the MOI checks, and the presentation

    Args:
        labelled_vcf (str): path to the VCF created by Hail runtime
        pedigree (str): path to the pedigree file
        input_path (str): path to the input file, logged in metadata
        output (str): path to JSON file to write
        prior_job (Job): to depend on, or None
        participant_panels (str): Optional, path to pheno-matched panels
    """

    results_job = get_batch().new_job(name='MOI tests')
    set_job_resources(results_job, prior_job=prior_job)

    gene_filter_files = (
        f'--participant_panels {participant_panels} ' if participant_panels else ''
    )

    validation_script_path = get_git_root_relative_path_from_absolute(validate_categories.__file__)
    html_script_path = get_git_root_relative_path_from_absolute(html_builder.__file__)

    results_command = (
        f'python3 {validation_script_path} '
        f'--labelled_vcf {labelled_vcf} '
        f'--panelapp {PANELAPP_JSON_OUT} '
        f'--pedigree {pedigree} '
        f'--out_json {output} '
        f'--input_path {input_path} '
        f'{gene_filter_files}'
    )
    logging.info(f'Results command: {results_command}')
    results_job.command(results_command)
    return results_job


def handle_result_presentation_job(
    prior_job: Job | None = None, **kwargs
) -> Job | None:
    """
    run the presentation element
    allow for selection of the presentation script and its arguments

    Note: The model here is to allow other non-CPG sites/users to
          implement their own presentation scripts, and to allow for the
          same method to be shared by all users. The contract here is that
          the presentation script must one or more named arguments, and
          the argument name must match the name passed to this method,
          i.e. `--panelapp {kwargs['panelapp']} `

          The contract also requires that new presentation scripts must
          not inactivate others, i.e. a runtime configuration setting
          should allow a user to select from any of the available scripts
          based on a config parameter.

    This isn't a super slick implementation, as there are no other users
    of this method, but it's a start. Alternative scripts will have to be
    created in code, at which point the script and this little mapping will
    both have to be updated.

    kwargs currently in use:
        - results: the JSON of results created by validate_categories.py
        - panelapp: the JSON of panelapp data
        - pedigree: the pedigree file (file accessible within the batch)
        - output: the output file path

    Args:
        prior_job (Job): used in workflow dependency setting
        kwargs (): key-value arguments for presentation script
    Returns:
        The associated job
    """

    # if a new script is added, it needs to be registered here to become usable
    scripts_and_inputs = {
        'cpg': (html_builder.__file__, ['results', 'panelapp', 'pedigree', 'output'])
    }

    output_mode = get_config()['workflow'].get('presentation', 'cpg')

    # if we don't have a valid method, return the prior job
    if output_mode not in scripts_and_inputs:
        logging.warning(f'Invalid presentation mode: {output_mode}')
        return prior_job

    # extract the required inputs for the selected script
    script, required_inputs = scripts_and_inputs[output_mode]

    # set the panelapp global variable in kwargs
    kwargs['panelapp'] = PANELAPP_JSON_OUT

    display = get_batch().new_job(name='Result Presentation')
    set_job_resources(display, prior_job=prior_job)

    # assemble command from relevant variables
    script_params = ' '.join(
        [f'--{named_input} {kwargs[named_input]} ' for named_input in required_inputs]
    )
    html_command = f'python3 {script} {script_params}'

    logging.info(f'HTML generation command: {html_command}')
    display.command(html_command)
    return display


def handle_registration_jobs(
    files: list[str], registry: str, pedigree: str, prior_job: Job | None = None
):
    """
    Take a list of files and register them using the defined method.
    This registration is within a metadata DB, used to track analysis
    products, and the samples they correspond to.

    Note: Similar contract to the one as defined above in
          handle_result_presentation_job - the `registrars` mapping
          should contain all valid registration scripts, and an ID
          for each. At runtime the user should be able to select any
          registered scripts using a config parameter. If an invalid
          registrar is selected, nothing will be done.

    Args:
        files (list[str]): all files to register from this analysis
        registry (str): registration service to use
        pedigree (str): path to a pedigree file (copied into batch)
        prior_job (Job): set workflow dependency if required
    """

    # dictionary with all known registration services
    registrars = {'metamist': metamist_registration.__file__}

    # if we don't have a valid method, return the prior job
    if registry not in registrars:
        logging.error(f'Invalid registration mode: {registry}')
        return

    # create a new job that will run even if the rest of the workflow fails
    registration_job = get_batch().new_job(name='register_results')
    set_job_resources(registration_job, prior_job=prior_job)
    registration_job.always_run(True)

    metadata_command = (
        f'python3 {registrars[registry]} --pedigree {pedigree} {" ".join(files)}'
    )

    logging.info(f'Metadata registration command: {metadata_command}')
    registration_job.command(metadata_command)


def main(
    input_path: str,
    pedigree: str,
    participant_panels: str | None,
    singletons: bool = False,
    skip_annotation: bool = False,
):
    """
    main method, which runs the full reanalysis process

    Args:
        input_path (str): path to the VCF/MT
        pedigree (str): family file for this analysis
        participant_panels (str): file containing panels-per-family (optional)
        singletons (bool): run as Singletons (with appropriate output paths)
        skip_annotation (bool): if the input is annotated, don't re-run
    """

    assert to_path(
        input_path
    ).exists(), f'The provided path {input_path!r} does not exist or is inaccessible'

    """
    Run a single VEP job.
    """
    out_format='json'
    tmp_prefix=to_path(output_path('vep_temp', 'tmp'))
    vep_ht_tmp = output_path('vep_annotations.ht', 'tmp')
    out_path=to_path(vep_ht_tmp)
    b=get_batch()
    j = b.new_job(name="VEP-test")
    j.image(image_path('vep'))
    STANDARD.set_resources(j, storage_gb=50, mem_gb=50, ncpu=16)

    vcf = b.read_input(str(input_path))

    j.declare_resource_group(
        output={'vcf.gz': '{root}.vcf.gz', 'vcf.gz.tbi': '{root}.vcf.gz.tbi'}
    )
    output = j.output['vcf.gz']

    # gcsfuse works only with the root bucket, without prefix:
    vep_mount_path = reference_path('vep_mount')
    data_mount = to_path(f'/{vep_mount_path.drive}')
    j.cloudfuse(vep_mount_path.drive, str(data_mount), read_only=True)
    vep_dir = data_mount / vep_mount_path.blob
    loftee_conf = {
        'loftee_path': '$LOFTEE_PLUGIN_PATH',
        'gerp_bigwig': f'{vep_dir}/gerp_conservation_scores.homo_sapiens.GRCh38.bw',
        'human_ancestor_fa': f'{vep_dir}/human_ancestor.fa.gz',
        'conservation_file': f'{vep_dir}/loftee.sql',
    }

    authenticate_cloud_credentials_in_job(j)
    cmd = f"""\
    ls {vep_dir}
    ls {vep_dir}/vep

    LOFTEE_PLUGIN_PATH=$MAMBA_ROOT_PREFIX/share/ensembl-vep
    FASTA={vep_dir}/vep/homo_sapiens/*/Homo_sapiens.GRCh38*.fa.gz

    vep \\
    --format vcf \\
    --{out_format} {'--compress_output bgzip' if out_format == 'vcf' else ''} \\
    -o {output} \\
    -i {vcf} \\
    --everything \\
    --allele_number \\
    --minimal \\
    --cache --offline --assembly GRCh38 \\
    --dir_cache {vep_dir}/vep/ \\
    --dir_plugins $LOFTEE_PLUGIN_PATH \\
    --fasta $FASTA \\
    --plugin LoF,{','.join(f'{k}:{v}' for k, v in loftee_conf.items())}
    """
    if out_format == 'vcf':
        cmd += f'tabix -p vcf {output}'

    j.command(
        command(
            cmd,
            setup_gcp=True,
            monitor_space=True,
        )
    )

    b.run(wait=False)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stderr,
    )
    logging.info(
        r"""Welcome To The
          ___  _____ ______
         / _ \|_   _|| ___ \
        / /_\ \ | |  | |_/ /
        |  _  | | |  |  __/
        | | | |_| |_ | |
        \_| |_/\___/ \_|
        """
    )

    parser = ArgumentParser()
    parser.add_argument('-i', help='variant data to analyse', required=True)
    parser.add_argument('--pedigree', help='in Plink format', required=True)
    parser.add_argument('--participant_panels', help='per-participant panel details')
    parser.add_argument(
        '--singletons',
        help='boolean, set if this run is a singleton pedigree',
        action='store_true',
    )
    parser.add_argument(
        '--skip_annotation',
        help='if set, annotation will not be repeated',
        action='store_true',
    )
    args = parser.parse_args()
    main(
        input_path=args.i,
        pedigree=args.pedigree,
        participant_panels=args.participant_panels,
        skip_annotation=args.skip_annotation,
        singletons=args.singletons,
    )
