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
            'PyYAML',
            'beautifulsoup4',
            'cashew>=0.2.0',
            'inflection',
            'orcid-python',
            'peewee>=2.0.0',
            'pyoai>=2.4.4',
            'python-modargs>=1.7',
            'requests>=2.0.0',
            'xlrd',
            'xlwt'
            ],
        name='oacensus',
        packages=find_packages(),
        url='',
        version=OACENSUS_VERSION
        )
