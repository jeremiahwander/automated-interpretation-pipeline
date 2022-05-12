import hail as hl
from cpg_utils.hail_batch import init_batch

init_batch()

mt = hl.read_matrix_table('gs://leo-tmp-au/leo-oom-debug/minimal.mt')

mt = mt.select_cols(
    hets=hl.agg.group_by(
        mt.gene_id,
        hl.agg.filter(mt.is_het, hl.agg.collect(mt.row_key)),
    )
)

mt.write('gs://leo-tmp-au/leo-oom-debug/out.mt', overwrite=True)
