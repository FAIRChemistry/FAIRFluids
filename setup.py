#!/usr/bin/env python3
"""
Setup script for FAIRFluids package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fairfluids",
    version="0.1.0",
    author="FAIRChemistry Team",
    author_email="contact@fairchemistry.org",
    description="A framework for creating FAIR fluid data documents with standardized metadata",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/FAIRChemistry/FAIRFluids",
    project_urls={
        "Bug Reports": "https://github.com/FAIRChemistry/FAIRFluids/issues",
        "Source": "https://github.com/FAIRChemistry/FAIRFluids",
        "Documentation": "https://github.com/FAIRChemistry/FAIRFluids#readme",
    },
    packages=find_packages(include=["fairfluids", "fairfluids.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "viz": [
            "matplotlib>=3.10.0",
            "scipy>=1.16.0",
            "seaborn>=0.13.0",
        ],
        "neo4j": [
            "neo4j>=5.14.0",
        ],
        "workflows": [
            "matplotlib>=3.10.0",
            "scipy>=1.16.0",
            "seaborn>=0.13.0",
            "openpyxl>=3.1.0",
            "plotly>=5.17.0",
            "flask>=2.3.0",
            "pint>=0.25.0",
            "ipykernel>=6.29.0",
            "jupyter-client>=8.6.0",
            "nbconvert>=7.16.0",
            "nbformat>=5.10.0",
        ],
        "bayesian": [
            "numpyro>=0.20.0",
            "jax>=0.7.0",
            "jaxlib>=0.7.0",
            "arviz>=0.22.0",
            "arviz-plots>=1.0.0",
            "arviz-base>=1.0.0",
            "arviz-stats>=1.0.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ],
        "all": [
            "matplotlib>=3.10.0",
            "scipy>=1.16.0",
            "seaborn>=0.13.0",
            "neo4j>=5.14.0",
            "openpyxl>=3.1.0",
            "plotly>=5.17.0",
            "flask>=2.3.0",
            "pint>=0.25.0",
            "ipykernel>=6.29.0",
            "jupyter-client>=8.6.0",
            "nbconvert>=7.16.0",
            "nbformat>=5.10.0",
            "numpyro>=0.20.0",
            "jax>=0.7.0",
            "jaxlib>=0.7.0",
            "arviz>=0.22.0",
            "arviz-plots>=1.0.0",
            "arviz-base>=1.0.0",
            "arviz-stats>=1.0.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fairfluids=fairfluids.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fairfluids": ["*.json", "*.xml", "*.xsd"],
    },
    keywords="chemistry fluids FAIR data metadata thermodynamics",
    zip_safe=False,
)
