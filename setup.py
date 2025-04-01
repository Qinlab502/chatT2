from setuptools import setup, find_packages

setup(
    name="chatt2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "cloudinary==1.42.2",
        "fuzzywuzzy==0.18.0",
        "nltk==3.8.1",
        "numpy==1.24.3",
        "openai==1.70.0",
        "pandas==1.4.2",
        "pymsaviz==0.5.0",
        "qdrant_client==1.13.3",
        "rank_bm25==0.2.2",
        "Requests==2.32.3",
        "SQLAlchemy==1.4.41",
        "bumpy==1.24.4",
    ],
    author="WANG YIHAN",
    python_requires="==3.8.*",  # This project currently supports Python 3.8 only.
)
