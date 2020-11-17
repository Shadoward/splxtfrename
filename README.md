# Rename the .all files using the *.fbf or *.fbz

## Introduction

This python script will remane the .xtf and create a log based on the *-Position.fbf or *-.fbz file.

## Setup

Several modules need to be install before using the script. You will need:

+ `$ pushd somepath\splxtfremane`
+ `$ pip install .`

## Usage

```
usage: splxtfrename.py [-h] [-r] [-f] [-n] xtfFolder splFolder splPosition

Rename the *.xtf files using the *-position.fbf or .fbz files

positional arguments:
  xtfFolder    xtfFolder (str): XTF folder path. This is the path where the *.xtf files to process are.
  splFolder    splFolder (str): SPL folder path. This is the path where the *.fbf/*.fbz files to process are.
  splPosition  splPosition (str): SPL postion file to be use to rename the *.xtf.

optional arguments:
  -h, --help          show this help message and exit
  -r, --recursive     Search recursively for XTF files.
  -f, --fbz           If FBZ, use this argument.
  -n, --rename        If you need to rename the files, use this argument.

Example:
 To rename the *.xtf file use python splxtfremane.py -r -f -n c:/temp/xtf/ c:/temp/fbf/ FugroBrasilis-CRP-Position
```

## Export products

+ Rename the *.xtf files
+ CSV logs files with all information needed to QC the data
  + Duplicate_XTF_Log.csv (XTF duplicated data)
  + NoLineNameFound_log.csv (SPL Session that do not have LineName information)
  + Full_XTF_Log.csv (Full logged data)
  + LineName_XTF_Log.csv (Log used to compare the LineName between sensor)

## TO DO
