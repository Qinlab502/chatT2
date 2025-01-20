from pathlib import Path

root = Path(__file__) / ".."
cwd = Path.cwd()

structure_database_file = "sqlite:///" + (root / "structure_database/chat_t2_database_v3.db").resolve().relative_to(cwd).as_posix()

articles_table_file = (root / "structure_database/articles_table_v3.xlsx").resolve().relative_to(cwd).as_posix()
vector_database_path = (root / "vector_database/vector_storage_512_json").resolve().relative_to(cwd).as_posix() + "/"

dynamic_images_cache_path = (root / "images_database/dynamic").resolve().relative_to(cwd).as_posix() + "/"
static_images_cache_path = (root / "images_database/static").resolve().relative_to(cwd).as_posix() + "/"


fasta_nucleotide_text = (root / "function_repository/gene_function_annotation/fasta_nucleotide_text.fasta").resolve().relative_to(cwd).as_posix()
fasta_protein_text = (root / "function_repository/gene_function_annotation/fasta_protein_text.fasta").resolve().relative_to(cwd).as_posix()
annotation_result_file = (root / "function_repository/gene_function_annotation/annotation_result.txt").resolve().relative_to(cwd).as_posix()


if __name__ == "__main__":
    print(structure_database_file, type(structure_database_file))
    print(articles_table_file, type(articles_table_file))
    print(vector_database_path, type(vector_database_path))
