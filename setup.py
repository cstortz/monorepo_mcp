#!/usr/bin/env python3
"""
Setup script for Monorepo MCP Server
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="monorepo-mcp-server",
    version="1.0.0",
    description="A monorepo structure for Model Context Protocol (MCP) servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Monorepo MCP Team",
    author_email="team@example.com",
    url="https://github.com/your-org/monorepo-mcp-server",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: System :: Networking",
    ],
    keywords="mcp, model-context-protocol, server, database, monorepo",
    project_urls={
        "Bug Reports": "https://github.com/your-org/monorepo-mcp-server/issues",
        "Source": "https://github.com/your-org/monorepo-mcp-server",
        "Documentation": "https://github.com/your-org/monorepo-mcp-server#readme",
    },
    entry_points={
        "console_scripts": [
            "postgres-mcp-server=servers.postgres_server.start:main",
            "mysql-mcp-server=servers.mysql_server.start:main",
            "redis-mcp-server=servers.redis_server.start:main",
        ],
    },
)
