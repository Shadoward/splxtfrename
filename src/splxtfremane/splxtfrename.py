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
import math

# progress bar
import time
from contextlib import redirect_stderr
import io
from tqdm import tqdm

# GUI
from gooey import Gooey, GooeyParser

# 417574686f723a205061747269636520506f6e6368616e74
####### Code #######
# this needs to be *before* the @Gooey decorator!
# (this code allows to only use Gooey when no arguments are passed to the script)
if len(sys.argv) >= 2:
    if not '--ignore-gooey' in sys.argv:
        sys.argv.append('--ignore-gooey')
        cmd = True 
    else:
        cmd = False  


# GUI Configuration
@Gooey(
    program_name='Rename *.XTF using *.FBF/FBZ file',
    progress_regex=r"^progress: (?P<current>\d+)/(?P<total>\d+)$",
    progress_expr="current / total * 100",
    hide_progress_msg=True,
    timing_options={        
        'show_time_remaining':True,
        'hide_time_remaining_on_complete':True
        },
    tabbed_groups=True,
    navigation='Tabbed',
    header_bg_color = '#95ACC8',
    #body_bg_color = '#95ACC8',
    menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'SPL XTF Rename',
                'description': 'Rename *.XTF using *.FBF/FBZ file',
                'version': '0.2.0',
                'copyright': '2020',
                'website': 'https://github.com/Shadoward/splxtfrename',
                'developer': 'patrice.ponchant@fugro.com',
                'license': 'MIT'
                }]
        },{
        'name': 'Help',
        'items': [{
            'type': 'Link',
            'menuTitle': 'Documentation',
            'url': ''
            }]
        }]
    )

def main():
    desc = "Rename the *.xtf files using the *-position.fbf or .fbz files"    
    parser = GooeyParser(description=desc)
    required = parser.add_argument_group('Required')
    optional = parser.add_argument_group('Optional')    
    # Optional Arguments
    optional.add_argument(
        '-r', '--recursive',
        metavar='Recurse into the subfolders?', 
        action='store_true', 
        default=True, 
        dest='recursive', 
        help='Yes')
    optional.add_argument(
        '-f', '--fbz',
        metavar='SPL Format is FBZ?',
        action='store_true', 
        default=False, 
        dest='fbfFormat', 
        help='Yes')
    optional.add_argument(
        '-n', '-rename',
        metavar='Rename the XTF?', 
        action='store_true', 
        default=False, 
        dest='rename', 
        help='Yes')
    # Required Arguments
    required.add_argument(
        #'--xtfFolder', 
        #action='store',
        dest='xtfFolder',        
        metavar='XTF Folder Path',
        help='XTF Root path. This is the path where the *.xtf files to process are.',
        default='C:\\Users\\patrice.ponchant\\Downloads\\XTF', 
        widget='DirChooser',
        type=str,
        gooey_options=dict(full_width=True,))
    required.add_argument(
        #'--splFolder', 
        #action='store',
        dest='splFolder',       
        metavar='SPL Root Path', 
        help='This is the path where the *.fbf/*.fbz files to process are. (Root Session Folder)',
        default='C:\\Users\\patrice.ponchant\\Downloads\\NEL',
        #default='S:\\JOBS\\2020\\20030002_Shell_FBR_MF\\B2B_FromVessel\\Navigation\\Starfix_Logging\\RawData', 
        widget='DirChooser',
        type=str,
        gooey_options=dict(full_width=True,))
    required.add_argument(
        #'--splPosition', 
        #action='store',
        dest='splPosition',
        metavar='SPL Position File Name', 
        widget='TextField',
        type=str,
        default='FugroBrasilis-CRP-Position',
        help='SPL position file to be use to rename the *.xtf without extention.',
        gooey_options=dict(full_width=True,))
        
    args = parser.parse_args()
    process(args, cmd)

def process(args, cmd):
    """
    Uses this if called as __main__.
    """
    xtfFolder = args.xtfFolder
    splFolder = args.splFolder
    splPosition = args.splPosition
    vessel = splPosition.split('-')[0]
    
    # Defined Dataframe
    dfSPL = pd.DataFrame(columns = ["Session Start", "Session End", "SPL LineName", "Vessel Name"])
    dfXTF = pd.DataFrame(columns = ["Session Start", "Session End", "Vessel Name", "SSS Start", "FileName in XTF",
                                    "FilePath", "SSS FileName", "SPL LineName", "SSS New LineName"]) 
    dftmp = pd.DataFrame(columns = ["Session Start", "Session End", "Vessel Name", "SSS Start", "FileName in XTF",
                                    "FilePath", "SSS FileName", "SPL LineName", "SSS New LineName"])    
    dfer = pd.DataFrame(columns = ["SPLPath"])
    
    # Check if SPL is a position file   
    if splPosition.find('-Position') == -1:
        print (f"The SPL file {splPosition} is not a position file, quitting")
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
     
    nowSPL = datetime.datetime.now() # record time of the subprocess   
    if args.fbfFormat:
        splListFile = glob.glob(splFolder + "\\**\\" + splPosition + ".fbz", recursive=True)
        print('')
        print(f'A total of {splListFile} *.fbf/fbz and {xtfListFile} *.xtf files will be processed.')
        print('')
        print('Reading the FBZ Files')
        if cmd: # to have a nice progress bar in the cmd  
            pbar = tqdm(total=len(splListFile))
        else:
            print(f"Note: Output show file counting every {math.ceil(len(splListFile)/10)}")            
        for index, n in enumerate(splListFile):              
            SessionStart, SessionEnd, LineName, er = FBZ2CSV(n , splFolder)
            dfSPL = dfSPL.append(pd.Series([SessionStart, SessionEnd, LineName, vessel], 
                                    index=dfSPL.columns ), ignore_index=True)
            if er:      
                dfer = dfer.append(pd.Series([er], index=dfer.columns ), ignore_index=True)            
            if cmd:
                pbar.update(1)
            else:
                print_progress(index, len(splListFile)) # to have a nice progress bar in the GUI
                if index % math.ceil(len(splListFile)/10) == 0: # decimate print
                    print(f"Files Process: {index+1}/{len(splListFile)}")                    
        if cmd:
            pbar.close()
        else:
            print("Subprocess Duration: ", (datetime.datetime.now() - nowSPL))
    else:
        splListFile = glob.glob(splFolder + "\\**\\" + splPosition + ".fbf", recursive=True)
        print('')
        print(f'A total of {len(splListFile)} *.fbf/fbz and {len(xtfListFile)} *.xtf files will be processed.')
        print('')
        print('Reading the FBF Files')
        if cmd: # to have a nice progress bar in the cmd  
            pbar = tqdm(total=len(splListFile))
        else:
            print(f"Note: Output show file counting every {math.ceil(len(splListFile)/10)}")             
        for index, n in enumerate(splListFile):              
            SessionStart, SessionEnd, LineName, er = FBF2CSV(n , splFolder)
            dfSPL = dfSPL.append(pd.Series([SessionStart, SessionEnd, LineName, vessel], 
                                    index=dfSPL.columns ), ignore_index=True)
            if er:      
                dfer = dfer.append(pd.Series([er], index=dfer.columns ), ignore_index=True)            
            if cmd:
                pbar.update(1)
            else:
                print_progress(index, len(splListFile)) # to have a nice progress bar in the GUI                
                if index % math.ceil(len(splListFile)/10) == 0: # decimate print
                    print(f"Files Process: {index+1}/{len(splListFile)}")                    
        if cmd:
            pbar.close()
        else:
            print("Subprocess Duration: ", (datetime.datetime.now() - nowSPL))

    # Format datetime
    dfSPL['Session Start'] = pd.to_datetime(dfSPL['Session Start'], format='%d/%m/%Y %H:%M:%S.%f') # format='%d/%m/%Y %H:%M:%S.%f' format='%Y/%m/%d %H:%M:%S.%f' 
    dfSPL['Session End'] = pd.to_datetime(dfSPL['Session End'], format='%d/%m/%Y %H:%M:%S.%f')
           
    print('')
    print('Reading the XTF File')
    nowXTF = datetime.datetime.now()  # record time of the subprocess 
    if cmd: # to have a nice progress bar in the cmd  
        pbar = tqdm(total=len(xtfListFile))
    else:
        print(f"Note: Output show file counting every {math.ceil(len(xtfListFile)/10)}")  
    for index, f in enumerate(xtfListFile):
        # Open the XTF file for reading by creating a new XTFReader class and passin in the filename to open.
        # The reader will read the initial header so we can get to grips with the file contents with ease. 
        r = XTFReader(f)            
        # print the XTF file header information.  This gives a brief summary of the file contents.
        pingHdr = r.readPacket()
        if pingHdr != None:
            XTFStarttime = datetime.datetime(pingHdr.Year, pingHdr.Month, pingHdr.Day, pingHdr.Hour, pingHdr.Minute, pingHdr.Second, pingHdr.HSeconds * 10000)
            FileNameinXTF = r.XTFFileHdr.ThisFileName
        
        XTFName = os.path.splitext(os.path.basename(f))[0] 
        dfXTF = dfXTF.append(pd.Series(["", "", "", XTFStarttime, FileNameinXTF, f, XTFName, "", ""], 
                    index=dfXTF.columns ), ignore_index=True)    
        r.rewind()
        r.close()
        if cmd:
            pbar.update(1)
        else:
            print_progress(index, len(xtfListFile)) # to have a nice progress bar in the GU            
            if index % math.ceil(len(xtfListFile)/10) == 0: # decimate print
                print(f"Files Process: {index+1}/{len(xtfListFile)}")                 
    if cmd:
        pbar.close()
    else:
        print("Subprocess Duration: ", (datetime.datetime.now() - nowXTF))

    # Format datetime
    dfXTF['SSS Start'] = pd.to_datetime(dfXTF['SSS Start'], unit='s')  # format='%d/%m/%Y %H:%M:%S.%f' format='%Y/%m/%d %H:%M:%S.%f'
        
    print('')
    print('Listing and Renaming the XTF files')
    nowRename = datetime.datetime.now()  # record time of the subprocess 
    if cmd: # to have a nice progress bar in the cmd
        if args.rename:  
            pbar = tqdm(total=len(xtfListFile))
    else:
        if args.rename:
            print(f"Note: Output show file counting every {math.ceil(len(xtfListFile)/10)}")  
    for index, row in dfSPL.iterrows():                  
        Start = row['Session Start']
        End = row['Session End']
        Name = row['SPL LineName']   
        dffilter = dfXTF[dfXTF['SSS Start'].between(Start, End)]
        for index, el in dffilter.iterrows():
            XTFFile =  el['FilePath']
            XTFStartTime = el['SSS Start']
            FileNameinXTF = el['FileName in XTF'] 
            FolderName = os.path.split(XTFFile)[0]
            XTFName = os.path.splitext(os.path.basename(XTFFile))[0]                               
            NewName = FolderName + '\\' + XTFName + '_' + Name + '.xtf'
            dftmp = dftmp.append(pd.Series([Start, End, vessel, XTFStartTime, FileNameinXTF, XTFFile, XTFName, Name, NewName], 
                                index=dftmp.columns ), ignore_index=True)
            # rename the *.xtf file           
            if args.rename:
                if cmd:
                    os.rename(XTFFile, NewName)
                    pbar.update(1)
                else:
                    os.rename(XTFFile, NewName)
                    print_progress(index, len(xtfListFile)) # to have a nice progress bar in the GU            
                    if index % math.ceil(len(xtfListFile)/10) == 0: # decimate print
                        print(f"Files Process: {index+1}/{len(xtfListFile)}")                                
    if not args.rename:
        print("No file was rename. Option Rename was unselected")
    if cmd:
        pbar.close()
    else:
        print("Subprocess Duration: ", (datetime.datetime.now() - nowRename))
                
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
        print(f"A total of {len(duplicate)/2} *.xtf was/were duplicated.")
        print("Please check the Duplicate_SSS_Log.csv for more information.")
        print("The first *.xtf occurrence was renamed.")
        duplicate.to_csv(xtfFolder + "Duplicate_SSS_Log.csv", index=True)
        dftmp = dftmp.drop_duplicates(subset='SSS Start', keep='first')
        dfXTF = dfXTF.drop_duplicates(subset='SSS Start', keep='first')
   
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
    
# from https://www.pakstech.com/blog/python-gooey/
def print_progress(index, total):
    print(f"progress: {index+1}/{total}")
    sys.stdout.flush()
  
if __name__ == "__main__":
    now = datetime.datetime.now() # time the process
    main()
    print('')
    print("Process Duration: ", (datetime.datetime.now() - now)) # print the processing time. It is handy to keep an eye on processing performance.