from pathlib import Path

root = Path(__file__) / ".."
cwd = Path.cwd()


fasta_nucleotide_text = (root / "gene_function_annotation/fasta_nucleotide_text.fasta").resolve().relative_to(cwd).as_posix()
fasta_protein_text = (root / "gene_function_annotation/fasta_protein_text.fasta").resolve().relative_to(cwd).as_posix()
annotation_result_file = (root / "gene_function_annotation/annotation_result.txt").resolve().relative_to(cwd).as_posix()
