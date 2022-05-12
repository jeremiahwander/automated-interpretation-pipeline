import asyncio
import hailtop.batch as hb
import hail as hl

def run():
    BILLING_PROJECT = 'test'
    REMOTE_TMPDIR = 'gs://leo-tmp-au/batch-tmp'

    asyncio.get_event_loop().run_until_complete(
        hl.init_batch(
            default_reference='GRCh38',
            billing_project=BILLING_PROJECT,
            remote_tmpdir=REMOTE_TMPDIR,
        )
    )

    mt = hl.read_matrix_table('gs://leo-tmp-au/leo-oom-debug/minimal.mt')

    mt = mt.select_cols(
        hets=hl.agg.group_by(
            mt.gene_id,
            hl.agg.filter(mt.is_het, hl.agg.collect(mt.row_key)),
        )
    )

    mt.write('gs://leo-tmp-au/leo-oom-debug/out.mt', overwrite=True)

if __name__ == '__main__':
    batch = hb.Batch()
    job = batch.new_python_job()
    job.ball(run)
    batch.run()

