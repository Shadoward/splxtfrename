# -*- coding: utf-8 -*-
# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_namespace_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

install_requires = [
    'pandas',
    'glob3',
    'tqdm',
    'gooey',
]

extras_require = {
    'build' : [
        'setuptools',
    ],
    'tests' : [],
}

setup(
    name='splxtfrename',
    version='0.4.0',
    description='Rename *.XTF using *.FBF/FBZ file',
    long_description=readme,
    author='Patrice Ponchant',
    author_email='patrice.ponchant@fugro.com',
    include_package_data = True,
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['tests'],
    url='',
    license=license,
    packages=find_namespace_packages(where='src'),
    package_dir={'': 'src'},
    keywords='FBF FBZ XTF SideScanSonar Rename',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering'
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

