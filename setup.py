from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="chinese-economic-headwinds-fix",
    version="1.0.0",
    author="Economic Headwinds Fix Team",
    author_email="contact@economic-headwinds-fix.org",
    description="Comprehensive technical solution for China's economic challenges",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/economic-headwinds-fix/chinese-economic-headwinds-fix",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=2.0.0",
        ],
        "data": [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "scikit-learn>=1.3.0",
            "statsmodels>=0.14.0",
            "prophet>=1.1.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "economic-fix-api=src.api.main:app",
            "economic-fix-test=test_economic_headwinds:main",
            "economic-fix-ingest=src.data_lake.ingestion.economic_data:main",
        ],
    },
    include_package_data=True,
    project_urls={
        "Bug Reports": "https://github.com/economic-headwinds-fix/chinese-economic-headwinds-fix/issues",
        "Source": "https://github.com/economic-headwinds-fix/chinese-economic-headwinds-fix",
        "Documentation": "https://economic-headwinds-fix.github.io/docs/",
    },
)
