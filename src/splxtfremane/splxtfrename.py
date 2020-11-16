# -*- coding: utf-8 -*-
###############################################################
# Author:       patrice.ponchant@furgo.com  (Fugro Brasil)    #
# Created:      04/11/2020                                    #
# Python :      3.x                                           #
###############################################################

# The future package will provide support for running your code on Python 2.6, 2.7, and 3.3+ mostly unchanged.
# http://python-future.org/quickstart.html
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from pathlib import Path
path = Path(__file__).resolve().parents[1]

# https://github.com/pktrigg/pyxtf
from pyXTF import *

##### For the basic function #####
import datetime
import sys
from pathlib import Path
import glob
import os
import subprocess

import pandas as pd

from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

# progress bar
from tqdm import *

# 417574686f723a205061747269636520506f6e6368616e74
####### Code #######
def main():
    parser = ArgumentParser(description='Rename the *.xtf files using the *-position.fbf or .fbz files',
        epilog='Example: \n To rename the *.xtf file use python splxtfremane.py -r -fbz c:/temp/xtf/ c:/temp/fbf/ FugroBrasilis-CRP-Position \n',
        formatter_class=RawTextHelpFormatter)    
    parser.add_argument('-r', action='store_true', default=False, dest='recursive', help='Search recursively for XTF files.')
    parser.add_argument('-fbz', action='store_true', default=False, dest='fbfFormat', help='If FBZ, use this argument.')
    parser.add_argument('xtfFolder', action='store', help='xtfFolder (str): XTF folder path. This is the path where the *.XTF files to process are.')
    parser.add_argument('splFolder', action='store', help='splFolder (str): SPL folder path. This is the path where the *.fbf/*.fbz files to process are.')
    parser.add_argument('SPLposition', action='store', help='SPLposition (str): SPL postion file to be use to rename the *.xtf.')
    
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    process(args)

def process(args):
    """
    Uses this if called as __main__.
    """
    xtfFolder = args.xtfFolder
    splFolder = args.splFolder
    SPLposition = args.SPLposition
    vessel = SPLposition.split('-')[0]
    
    # Defined Dataframe
    dfSPL = pd.DataFrame(columns = ["Session Start", "Session End", "SPL LineName", "Vessel Name"])
    dfXTF = pd.DataFrame(columns = ["Session Start", "Session End", "Vessel Name", "SSS Start", "numberOfBytes", "STX", 
                                    "EMModel", "FilePath", "SSS FileName", "SPL LineName", "SSS New LineName"]) 
    dftmp = pd.DataFrame(columns = ["Session Start", "Session End", "Vessel Name", "SSS Start", "numberOfBytes", "STX", 
                                    "EMModel", "FilePath", "SSS FileName", "SPL LineName", "SSS New LineName"])    
    dfer = pd.DataFrame(columns = ["SPLPath"])
    
    # Check if SPL is a position file   
    if SPLposition.find('-Position') == -1:
        print (f"The SPL file {SPLposition} is not a position file, quitting")
        exit()

    print('')
    print('Listing the files. Please wait....')
    xtfListFile = []
    if args.recursive:
        exclude = ['DNP', 'DoNotProcess']
        # exclude = set(['New folder', 'Windows', 'Desktop'])
        for root, dirs, files in os.walk(xtfFolder, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            for filename in files:
                if filename.endswith('xtf'):
                    filepath = os.path.join(root, filename)
                    xtfListFile.append(filepath)
    else:
        xtfListFile = glob.glob(xtfFolder + "\\*.xtf")
        
    if args.fbfFormat:
        splListFile = glob.glob(splFolder + "\\**\\" + SPLposition + ".fbz", recursive=True)
        print('')
        print(f'A total of {splListFile} *.fbf/fbz and {xtfListFile} *.xtf files will be processed.')
        print('')
        print('Reading the FBZ Files')
        with tqdm(total=len(splListFile)) as pbar:
            for n in splListFile:              
                SessionStart, SessionEnd, LineName, er = FBZ2CSV(n , splFolder)
                dfSPL = dfSPL.append(pd.Series([SessionStart, SessionEnd, LineName, vessel], 
                                       index=dfSPL.columns ), ignore_index=True)
                if er:      
                    dfer = dfer.append(pd.Series([er], index=dfer.columns ), ignore_index=True)
                pbar.update(1) 
    else:
        splListFile = glob.glob(splFolder + "\\**\\" + SPLposition + ".fbf", recursive=True)
        print('')
        print(f'A total of {len(splListFile)} *.fbf/fbz and {len(xtfListFile)} *.xtf files will be processed.')
        print('')
        print('Reading the FBF Files')
        with tqdm(total=len(splListFile)) as pbar:
            for n in splListFile:
                SessionStart, SessionEnd, LineName, er = FBF2CSV(n , splFolder)
                dfSPL = dfSPL.append(pd.Series([SessionStart, SessionEnd, LineName, vessel], 
                                       index=dfSPL.columns ), ignore_index=True)
                if er:      
                    dfer = dfer.append(pd.Series([er], index=dfer.columns ), ignore_index=True)
                pbar.update(1)          

    # Format datetime
    dfSPL['Session Start'] = pd.to_datetime(dfSPL['Session Start'], format='%d/%m/%Y %H:%M:%S.%f') # format='%d/%m/%Y %H:%M:%S.%f' format='%Y/%m/%d %H:%M:%S.%f' 
    dfSPL['Session End'] = pd.to_datetime(dfSPL['Session End'], format='%d/%m/%Y %H:%M:%S.%f')
           
    print('')
    print('Reading the XTF File')
    with tqdm(total=len(xtfListFile)) as pbar:
        for f in xtfListFile:
            # Open the XTF file for reading by creating a new XTFReader class and passin in the filename to open.
            # The reader will read the initial header so we can get to grips with the file contents with ease. 
            r = XTFReader(f)
            
            # print the XTF file header information.  This gives a brief summary of the file contents.
            #while r.moreData():
            pingHdr = r.readPacket()
            if pingHdr != None:
                XTFStarttime = datetime.datetime(pingHdr.Year, pingHdr.Month, pingHdr.Day, pingHdr.Hour, pingHdr.Minute, pingHdr.Second, pingHdr.HSeconds * 10000)
                print(XTFStarttime)
            sys.exit()
                   
            numberOfBytes, STX, typeOfDatagram, EMModel, RecordDate, RecordTime = r.readDatagramHeader() # read the common header for any datagram.
            #AllStartTime = to_timestamp(to_DateTime(RecordDate, RecordTime))           
            ALLName = os.path.splitext(os.path.basename(f))[0] 
            dfXTF = dfXTF.append(pd.Series(["","", "", AllStartTime, numberOfBytes, STX, EMModel, f, ALLName, "", ""], 
                        index=dfXTF.columns ), ignore_index=True)    
            r.rewind()
            r.close()               
            pbar.update(1)

    # Format datetime
    dfXTF['SSS Start'] = pd.to_datetime(dfXTF['SSS Start'], unit='s')  # format='%d/%m/%Y %H:%M:%S.%f' format='%Y/%m/%d %H:%M:%S.%f'
        
    print('')
    print('Renaming the XTF files')
    with tqdm(total=len(xtfListFile)) as pbar:
        for index, row in dfSPL.iterrows():                  
            Start = row['Session Start']
            End = row['Session End']
            Name = row['SPL LineName']   
            dffilter = dfXTF[dfXTF['SSS Start'].between(Start, End)]
            for index, el in dffilter.iterrows():
                XTFFile =  el['FilePath']
                XTFStartTime = el['SSS Start']
                numberOfBytes = el['numberOfBytes']
                STX = el['STX']
                EMModel = el['EMModel']   
                FolderName = os.path.split(XTFFile)[0]
                XTFName = os.path.splitext(os.path.basename(XTFFile))[0]                               
                NewName = FolderName + '\\' + XTFName + '_' + Name + '.xtf'
                dftmp = dftmp.append(pd.Series([Start, End, vessel, XTFStartTime, numberOfBytes, STX, EMModel, XTFFile, XTFName, Name, NewName], 
                                    index=dftmp.columns ), ignore_index=True)
                # rename the *.xtf file           
                # if os.path.isfile(XTFFile):
                #     os.rename(XTFFile, NewName)        
                pbar.update(1)
                
    print('')
    print('Creating logs. Please wait....')
    # Format datetime
    dfXTF['Session Start'] = pd.to_datetime(dfXTF['Session Start'], unit='s')
    dfXTF['Session End'] = pd.to_datetime(dfXTF['Session End'], unit='s')
    
    if not dfer.empty:
        print("")
        print(f"A total of {len(dfer)} Session SPL has/have no Linename information.")
        print("Please check the NoLineNameFound_log.csv for more information.")
        print("The column LineName in Full_SSS_log.csv will contain NoLineName for the corresponding *.xtf")
        dfer.to_csv(xtfFolder + "NoLineNameFound_log.csv", index=True)  
       
    # Droping duplicated *.xtf and creating a log.
    duplicate = dftmp[dftmp.duplicated(subset='SSS Start', keep=False)]
    duplicate.sort_values('SSS Start')
    if not duplicate.empty:
        print("")
        print(f"A total of {len(duplicate)} *.xtf was/were duplicated.")
        print("Please check the Duplicate_SSS_Log.csv for more information.")
        print("The first *.xtf occurrence was renamed.")
        duplicate.to_csv(xtfFolder + "Duplicate_SSS_Log.csv", index=True)
        dftmp = dftmp.drop_duplicates(subset='SSS Start', keep='first')
   
    # Updated the final dataframe to export the log
    dfXTF.set_index('SSS Start', inplace=True)
    dftmp.set_index('SSS Start', inplace=True)
    dfXTF.update(dftmp)
    
    # Format datetime
    dfXTF['Session Start'] = pd.to_datetime(dfXTF['Session Start'], unit='s')
    dfXTF['Session End'] = pd.to_datetime(dfXTF['Session End'], unit='s')

    # Saving the file
    dfXTF.to_csv(xtfFolder + "Full_SSS_Log.csv", index=True)
    dfXTF.to_csv(xtfFolder + "LineName_SSS_Log.csv", index=True, columns=['Session End','Vessel Name','SPL LineName','SSS FileName'])
    print("")
    print(f'Logs can be found in {xtfFolder}.')

##### Convert NEL/FBF/FBZ to CSV #####
def NEL2CSV(Nelkey, NelFileName, Path):
    ##### Convert NEL to CSV #####
    FileName = os.path.splitext(os.path.basename(NelFileName))[0]    
    csvfilepath = Path + FileName + "_" + Nelkey + '.csv'
    cmd = 'for %i in ("' + NelFileName + '") do nel2asc -v "%i" ' + Nelkey + ' > ' + csvfilepath
    subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    #created the variables
    dfS = pd.read_csv(csvfilepath, header=None, skipinitialspace=True)
    LineStart = dfS.iloc[0][0]
    LineName = dfS.iloc[0][3]
    
    #cleaning
    os.remove(csvfilepath)
    
    return LineStart, LineName

def FBF2CSV(FBFFileName, Path):
    ##### Convert FBF to CSV #####
    
    FileName = os.path.splitext(os.path.basename(FBFFileName))[0]    
    fbffilepath = Path + FileName + '.csv'
    cmd = 'for %i in ("' + FBFFileName + '") do fbf2asc -i %i -o "' + fbffilepath + '"'
    subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    #subprocess.call(cmd, shell=True) ### For debugging
    
    #created the variables
    dfS = pd.read_csv(fbffilepath, header=None, skipinitialspace=True, na_values='NoLineNameFound')

    SessionStart = dfS.iloc[0][0]
    SessionEnd = dfS.iloc[-1][0]
    LineName = dfS.iloc[0][8]
    
    #cleaning  
    os.remove(fbffilepath)
    
    # checking if linename is empty as is use in all other process
    if pd.isnull(LineName):
        er = FBFFileName
        return SessionStart, SessionEnd, "NoLineNameFound", er       
    else:
        er = ""
        return SessionStart, SessionEnd, LineName, er

def FBZ2CSV(FBZFileName, Path):
    ##### Convert FBZ to CSV #####
    FileName = os.path.splitext(os.path.basename(FBZFileName))[0]    
    fbzfilepath = Path + FileName + '.csv'
    cmd = 'for %i in ("' + FBZFileName + '") do C:\ProgramData\Fugro\Starfix2018\Fugro.DescribedData2Ascii.exe %i > "' + fbzfilepath + '"'
    subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    #subprocess.call(cmd, shell=True) ### For debugging
    
    #created the variables
    dfS = pd.read_csv(fbzfilepath, header=None, skipinitialspace=True, na_values='NoLineNameFound')

    SessionStart = dfS.iloc[0][0]
    SessionEnd = dfS.iloc[-1][0]
    LineName = dfS.iloc[0][8]
    
    #cleaning  
    os.remove(fbzfilepath)
    
    #checking if linename is empty as is use in all other process
    if pd.isnull(LineName):
        er = FBZFileName
        return SessionStart, SessionEnd, "NoLineNameFound", er       
    else:
        er = ""
        return SessionStart, SessionEnd, LineName, er

  
if __name__ == "__main__":
    now = datetime.datetime.now() # time the process
    main()
    print('')
    print("Process Duration: ", (datetime.datetime.now() - now)) # print the processing time. It is handy to keep an eye on processing performance.