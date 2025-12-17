from setuptools import setup, find_packages

setup(
    name="budgets",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.0.0",
        "requests>=2.28.0",
        "tqdm>=4.65.0",
        "reg-normalizer>=0.1.0",
        "pyarrow>=12.0.0",
        "openpyxl>=3.1.0",
        "boto3>=1.28.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "budgets=budgets.main:main",
        ],
    },
)

