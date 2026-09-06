"""Setup configuration for quantum_workspace package."""

from setuptools import find_packages, setup

setup(
    name="quantum-workspace",
    version="0.1.0",
    description="Professional quantum computing environment",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9,<=3.13",
    install_requires=[
        "numpy>=2.0",
        "scipy>=1.14",
        "pyyaml>=6.0",
        "pyqpanda3>=0.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.24",
            "ruff>=0.16",
        ],
    },
)
