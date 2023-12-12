"""Setup script for the package."""

from setuptools import setup, find_packages

setup(
    name="CAESURA",
    version="0.0.1",
    description="LM-driven query planning for multi-modal data systems.",
    url="https://github.com/DataManagementLab/caesura",
    author="Matthias Urban and Carsten Binnig",
    author_email="matthias.urban@cs.tu-darmstadt.de",
    license="MIT",
    packages=find_packages(),
)