# =============================================================================
# FILE PURPOSE:
# Standard setuptools configuration for packaging the GuardPVM Python SDK.
# Enables installing the SDK globally or into virtualenvs via `pip install .`.
# Run with: pip install -e src/guardpvm
# =============================================================================

from setuptools import setup, find_packages

setup(
    name="guardpvm",
    version="1.0.0",
    description="GuardPVM SDK - Step Quotas, Telemetry, and Zero-Division Recovery for Python",
    author="GuardPVM Team",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
