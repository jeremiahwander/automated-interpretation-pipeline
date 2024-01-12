"""
Method file for re-sorting clinvar annotations by codon

This makes the assumption that the annotated data here
has been generated by summarise_clinvar_entries.py:

- SNV only
- Clinvar Pathogenic only
- ClinVar decision/alleles/gold stars are in INFO
"""

import click

import hail as hl

from cpg_utils.hail_batch import init_batch


@click.command()
@click.option('--mt_path', help='Path to the annotated MatrixTable')
@click.option('--write_path', help='Path to export PM5 table')
def protein_indexed_clinvar(mt_path: str, write_path: str):
    """
    Takes a MatrixTable of annotated Pathogenic Clinvar Variants
    re-indexes the data to be queryable on Transcript and Codon
    writes the resulting Table to the specified path

    Args:
        mt_path (str): Path to annotated ClinVar MatrixTable
        write_path (str): location to write new file to
    """

    init_batch()

    vep_clinvar = hl.read_matrix_table(mt_path)
    vep_clinvar.describe()
    # 1. retain only relevant annotations
    vep_clinvar = vep_clinvar.rows()
    vep_clinvar = vep_clinvar.select(
        tx_csq=vep_clinvar.vep.transcript_consequences, info=vep_clinvar.clinvar
    )

    # 2. split rows out to separate transcript consequences
    vep_clinvar = vep_clinvar.explode(vep_clinvar.tx_csq)

    # 3. filter down to missense
    # a reasonable filter here would also include MANE transcripts
    vep_clinvar = vep_clinvar.filter(
        vep_clinvar.tx_csq.consequence_terms.contains('missense_variant')
    )

    # 4. squash the clinvar and protein content into single strings
    vep_clinvar.describe()
    vep_clinvar = vep_clinvar.annotate(
        clinvar_entry=hl.str('::').join(
            [
                hl.str(vep_clinvar.info.allele_id),
                hl.str(vep_clinvar.info.gold_stars),
            ]
        ),
        newkey=hl.str('::').join(
            [
                vep_clinvar.tx_csq.protein_id,
                hl.str(vep_clinvar.tx_csq.protein_start),
            ]
        ),
    )

    # 5. re-key table on transcript & residue
    vep_clinvar = vep_clinvar.key_by(vep_clinvar.newkey)

    # 6. collect all ClinVar annotations at each residue
    vep_clinvar = vep_clinvar.select(vep_clinvar.clinvar_entry).collect_by_key()

    # 7. squash the multiple clinvar entries back to a single string
    vep_clinvar = vep_clinvar.transmute(
        clinvar_alleles=hl.str('+').join(
            hl.set(hl.map(lambda x: x.clinvar_entry, vep_clinvar.values))
        )
    )

    # 8. write the table of all ENSP:residue#: Clinvar[+Clinvar,]
    vep_clinvar.write(write_path, overwrite=True)


if __name__ == '__main__':
    protein_indexed_clinvar()
