#!/usr/bin/env python3

import os

from cpg_utils.config import get_config
from cpg_utils.hail_batch import remote_tmpdir
import hailtop.batch as hb

QOB_SUB_SCRIPT = os.path.join(os.path.dirname(__file__), 'test_qob_sub.py')

def main(
    blob: str
):
    """
    main
    """

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

    j = batch.new_job()
    j.command('echo "Calling QoB test subscript."')
    j.command(f'python3 {QOB_SUB_SCRIPT}')

    batch.run(wait=False)


if __name__ == '__main__':
    main()  # pylint: disable=E1120


