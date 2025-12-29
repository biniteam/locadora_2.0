"""
Setup script para o Sistema de Locadora de Veículos
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read long description from README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="locadora-strealit",
    version="5.0.0",  # Major version bump for Supabase integration
    description="Sistema de Locadora de Veículos com Streamlit e Supabase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="J.A. MARCELLO & CIA LTDA",
    author_email="contato@locadora.com",
    url="https://github.com/seu-usuario/locadora_strealit",
    packages=find_packages(exclude=["tests*", "docs*"]),
    package_data={
        "": ["*.toml", "*.json", "*.sql"],
    },
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.10",  # Updated to match requirements.txt
    entry_points={
        "console_scripts": [
            "locadora=app:main",  # Updated from app8 to app
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
    ],
    keywords="locadora veiculos streamlit supabase",
    project_urls={
        "Source": "https://github.com/seu-usuario/locadora_strealit",
        "Bug Reports": "https://github.com/seu-usuario/locadora_strealit/issues",
    },
    # Optional dependencies for development
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
    },
)
