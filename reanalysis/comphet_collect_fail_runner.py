import hailtop.batch as hb

if __name__ == '__main__':
    BILLING_PROJECT = 'test'
    REMOTE_TMPDIR = 'gs://leo-tmp-au/batch-tmp'

    service_backend = hb.ServiceBackend(
        billing_project=BILLING_PROJECT, remote_tmpdir=REMOTE_TMPDIR
    )

    batch = hb.Batch(name='oom-heap-dump', backend=service_backend)
    job = batch.new_job()
    job.image('australia-southeast1-docker.pkg.dev/analysis-runner/images/driver:8f74e06257a75383689bc38ab3e88add6df8462c-hail-bb0dd360e4d546ff948c1d7b43614667e829be57')
    job.command('git clone https://github.com/populationgenomics/automated-interpretation-pipeline.git')
    job.command('python3 automated-interpretation-pipeline/reanalysis/comphet_collect_fail.py')
    batch.run(wait=False)

