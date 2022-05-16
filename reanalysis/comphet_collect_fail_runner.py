import hailtop.batch as hb

if __name__ == '__main__':
    #BILLING_PROJECT = 'test'
    BILLING_PROJECT = 'leonhardgruenschloss-trial'
    REMOTE_TMPDIR = 'gs://leo-tmp-au/batch-tmp'

    service_backend = hb.ServiceBackend(billing_project=BILLING_PROJECT, remote_tmpdir=REMOTE_TMPDIR)

    batch = hb.Batch(name='oom-heap-dump', backend=service_backend)
    job = batch.new_job()
    job.image('australia-southeast1-docker.pkg.dev/analysis-runner/images/driver:36c6d4548ef347f14fd34a5b58908057effcde82-hail-ad1fc0e2a30f67855aee84ae9adabc3f3135bd47')
    job.command('git clone -b comp_het_fail_again_leo https://github.com/populationgenomics/automated-interpretation-pipeline.git')
    job.command('python3 automated-interpretation-pipeline/reanalysis/comphet_collect_fail.py')
    batch.run(wait=False)

