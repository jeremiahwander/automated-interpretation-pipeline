import hailtop.batch as hb

if __name__ == '__main__':
    batch = hb.Batch()
    job = batch.new_job()
    job.image('gcr.io/hail-vdc/python-dill:3.7-slim')
    job.command('git clone https://github.com/populationgenomics/automated-interpretation-pipeline.git')
    job.command('python3 automated-interpretation-pipeline/reanalysis/comphet_collect_fail.py')
    batch.run(wait=False)

