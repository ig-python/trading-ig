from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyIG',
    version='1.0.0',
    description='IG Markets Trading API',
    long_description=long_description,
    url='https://github.com/th3sys/pyIG',
    author='Alexy Shelest',
    author_email='alexy@th3sys.com',
    license='MIT',
    platforms=['any'],
    classifiers=[
        'Programming Language :: Python :: 3.6'
    ],

    keywords='IG Markets API trading-api trading',

    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    install_requires=['pandas', 'requests', 'six', 'munch'],

    extras_require={
        'dev': ['check-manifest', 'nose'],
        'test': ['coverage', 'nose'],
    },
)
