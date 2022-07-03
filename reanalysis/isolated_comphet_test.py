"""
single script to check the compound-het failure on minimal data
"""

import logging
import sys
from argparse import ArgumentParser

import hail as hl

from cpg_utils.hail_batch import init_batch, output_path


def extract_comp_het_details(matrix: hl.MatrixTable) -> None:
    """
    docstring
    """
    logging.info('Extracting out the compound-het variant pairs')

    # set a new group of values as the key, so that we can collect on them easily
    ch_matrix = matrix.key_rows_by(matrix.locus, matrix.alleles, matrix.category_4_only)

    ch_matrix = ch_matrix.select_cols(
        hets=hl.agg.group_by(
            ch_matrix.info.gene_id,
            hl.agg.filter(ch_matrix.GT.is_het(), hl.agg.collect(ch_matrix.row_key)),
        )
    )

    tmp_path = output_path('leo_test_ch_matrix_hets', 'tmp')
    logging.info(f'Checkpointing to {tmp_path}')
    ch_matrix.write(tmp_path, overwrite=True)


def main(mt_in: str):
    """

    :param mt_in:
    :return:
    """

    # initiate Hail with upgraded driver spec.
    init_batch(
        driver_cores=8,
        driver_memory='highmem',
    )

    # load in the MT
    matrix = hl.read_matrix_table(mt_in)
    extract_comp_het_details(matrix=matrix)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stderr,
    )

    parser = ArgumentParser()
    parser.add_argument('--mt_input', required=True, help='path to the matrix table')
    args = parser.parse_args()
    main(mt_in=args.mt_input)
