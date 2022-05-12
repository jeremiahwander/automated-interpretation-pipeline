import hailtop.batch as hb

if __name__ == '__main__':
    BILLING_PROJECT = 'test'
    REMOTE_TMPDIR = 'gs://leo-tmp-au/batch-tmp'

    service_backend = hb.ServiceBackend(
        billing_project=BILLING_PROJECT, remote_tmpdir=REMOTE_TMPDIR
    )

    batch = hb.Batch(name='oom-heap-dump', backend=service_backend)
    job = batch.new_job()
    job.image('gcr.io/hail-vdc/python-dill:3.7-slim')
    job.command('git clone https://github.com/populationgenomics/automated-interpretation-pipeline.git')
    job.command('python3 automated-interpretation-pipeline/reanalysis/comphet_collect_fail.py')
    batch.run(wait=False)

