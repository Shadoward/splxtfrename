# Rename the .all files using the .nel

## Introduction
This python script will remane the .all in the folder based on the LineRunline nelgroup inside the .nel files.

## Setup
Several modules need to be install before using the script. You will need:
+ `$ pushd somepath\nelallremane`
+ `$ pip install .`

## Usage
```
usage: nelallrename.py [-h] allFolder nelFolder

Rename the *.all files using the LineRunline nelgroup inside the .nel files.

positional arguments:
  allFolder   allFolder (str): ALL folder path. This is the path where the *.all files to process are.
  nelFolder   nelFolder (str): NEl folder path. This is the path where the *.nel files to process are.

optional arguments:
  -h, --help  show this help message and exit

Example:
 To rename the *.all file use python nelallremane.py c:/temp/all/ c:/temp/nel/
```