from setuptools import setup

setup(
    name='de-identifier',
    version='0.1',
    packages=[''],
    package_dir={'': 'src'},
    install_requires=[
            'presidio_analyzer>2.2',
            'presidio_anonymizer>2.2',
            'flair>0.12'
        ],
    url='https://github.com/TRG-AI4Good/de-identifier',
    license='MIT',
    author='Mohammad Askari',
    author_email='askari@ucla.edu',
    description='PII de-identification from a given CSV file using two NERs, spaCy and Flair'
)
