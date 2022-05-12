import asyncio
import hail as hl

if __name__ == '__main__':
    BILLING_PROJECT = 'test'
    REMOTE_TMPDIR = 'gs://leo-tmp-au/batch-tmp'

    asyncio.get_event_loop().run_until_complete(
        hl.init_batch(
            default_reference='GRCh38',
            billing_project=BILLING_PROJECT,
            remote_tmpdir=REMOTE_TMPDIR,
            driver_cores=4,
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

