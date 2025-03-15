from setuptools import setup, find_packages

setup(
    name="moto-analysis-tool",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=4.2.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
        "mlxtend>=0.21.0",
        # Explicitly require the main app
        "moto-main-app>=1.0.0",  # Replace with the actual package name of main_app
    ],
    license="AGPL-3.0-only",
    python_requires=">=3.8",
)