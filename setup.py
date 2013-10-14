from setuptools import setup, find_packages
from oacensus.version import OACENSUS_VERSION

setup(
        classifiers=[
            "Development Status :: 4 - Beta"
            ],
        description='Open Access census and reporting utilities.',
        entry_points = {
            'console_scripts' : [
                'oacensus = oacensus.commands:run'
                ]
            },
        include_package_data = True,
        install_requires = [
            'dexy',
            'requests>=2.0.0',
            'orcid-python',
            ],
        name='oacensus',
        packages=find_packages(),
        url='',
        version=OACENSUS_VERSION
        )
