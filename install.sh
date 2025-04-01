echo "Installing Python dependencies..."
pip install .

echo "Installing external tools with conda..."
conda install -c conda-forge -c bioconda mmseqs2 -y
conda install conda-forge::mafft -y