#!/usr/bin/env python3
"""
Setup script for JARVIS project
This ensures the package installs correctly in editable mode
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
def read_requirements(filename):
    requirements_path = Path(__file__).parent / filename
    if requirements_path.exists():
        with open(requirements_path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="jarvis",
    version="0.0.1",
    description="JARVIS - Personal AI Assistant for macOS",
    author="Gabriel Gonzaga",
    python_requires=">=3.12",
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["jarvis*"]),
    include_package_data=True,
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
    },
    entry_points={
        "console_scripts": [
            "jarvis=jarvis.__main__:main",
        ],
    },
)