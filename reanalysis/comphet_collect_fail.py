import hail as hl
from cpg_utils.hail_batch import init_batch

init_batch()

mt = hl.read_matrix_table('gs://cpg-acute-care-test/leo-oom-debug/gene_id.mt')

mt = mt.select_cols(
    hets=hl.agg.group_by(
        mt.info.gene_id,
        hl.agg.filter(mt.is_het, hl.agg.collect(mt.row_key)),
    )
)

mt.write('gs://cpg-acute-care-test/leo-oom-debug/out.mt', overwrite=True)
