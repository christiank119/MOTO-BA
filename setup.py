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
        #"moto-main-app>=1.0.0",  # This has to be replaced actual package name of main_app when accually one exists 
    ],
    license="AGPL-3.0-only",
    python_requires=">=3.8",
)