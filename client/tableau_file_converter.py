import os
import shutil
import logging
from lxml import etree

import utils
import xmlintruder

def twbxFromTdeAndTds(baseDir, tempDirName, tdeFileName, tdsFileName, baseTwb):
    # Copy to twb temp directory
    shutil.copy(os.path.join(baseDir, tdeFileName), os.path.join(baseDir, tempDirName))

    # Manipulate the temp and save to the twb temp dir
    createTwbFromTds(baseDir, tempDirName, baseTwb, tdsFileName, tdeFileName)

    # Step x: Creat te twbx from twb + tde
    utils.createZip(os.path.join(baseDir, tempDirName), os.path.join(baseDir, tdsFileName.replace('tds', 'twbx')))

    # return twbx path 
    return os.path.join(baseDir, tdsFileName.replace('tds', 'twbx'))

def tdsxToTwbx(tdsxFileName,
                twbxFileName,\
                tempFileDir='tableau',\
                baseTwbFileName='emptywb.twb',\
                tdsxExtractDir='fromtdsx',\
                twbxDir='twbxtemp'):

    # Step1: Unzip tdsx
    # Crete temp dir if not exists
    if not os.path.exists(tdsxExtractDir):
        os.makedirs(tdsxExtractDir)

    utils.unzip(os.path.join(tempFileDir, tdsxFile), tdsxExtractDir)

    tdsxfiles = utils.getFiles(tdsxExtractDir)

    # Create a temp directory for the twbx to be generated
    if not os.path.exists(twbxDir):
        os.makedirs(twbxDir)

    tdefilename = None

    for tf in tdsxfiles:
        if tf.get('name').endswith('tde'):
            # Copy to twb temp directory
            shutil.copy(tf.get('full'), twbxDir)
            tdefilename = tf.get('full')
        else:
            # Manipulate the temp and save to the twb temp dir
            createTwbFromTds(
                os.path.join(tempFileDir, baseTwbFileName),\
                tf.get('full'), os.path.join(twbxDir, tf.get('name').replace('.tds', '.twb')),\
                tdefilename)

    # Step x: Creat te twbx from twb + tde
    utils.createZip(twbxDir, twbxFileName)

    os.chdir(working_directory_store)
    return os.path.join(twbxDir, twbxFileName)


def twbxToTdsx(baseDir, tempDirName, tdsFileName):
    logging.debug('Generate Tdsx from ' + os.path.join(baseDir, tdsFileName.replace('tds', 'twbx')))

    # remove all file from twbx temp directory
    utils.deleteall(os.path.join(baseDir, tempDirName))

    # extract twbx to twbxTemp dir
    utils.unzip(os.path.join(baseDir, tdsFileName.replace('tds', 'twbx')), os.path.join(baseDir, tempDirName))

    # get tde file
    # copy the original tds to this dir
    shutil.copy(os.path.join(baseDir, tdsFileName), os.path.join(baseDir, tempDirName))

    # find twb file from the twbx
    twbfiles = utils.getFiles(os.path.join(baseDir, tempDirName))
    twbfile = None
    for tf in twbfiles:
        if tf.get('name').endswith('twb'):
            twbfile = tf

    # copy twb database subtree back to the original tds file
    tdsxmlstr = utils.openfile(os.path.join(baseDir, tempDirName, tdsFileName))
    twbxmlstr = utils.openfile(os.path.join(baseDir, tempDirName, tdsFileName.replace('tds', 'twb')))
    
    tdsIntruder = xmlintruder.XmlIntruder(tdsxmlstr)
    twbIntruder = xmlintruder.XmlIntruder(twbxmlstr)

    # get tds datasource
    tdsDatasourceList = tdsIntruder.subtree('/datasource')

    # Store original twb datasource attributes
    attributes = None
    for ds in tdsDatasourceList:
        attributes = ds.attrib

    # read tds datasource tree
    twbDatasourceList = twbIntruder.subtree('/workbook/datasources/datasource')

    # copy twb datasource tag attributes with the tds attributes
    for twbds in twbDatasourceList:
        twbIntruder.deleteAllAttrib(twbds).addAllAttribs(twbds, attributes).insertInto('/workbook/datasources', twbds)
        tdsIntruder.settree(etree.tostring(twbds))

    tdsIntruder.write(os.path.join(baseDir, tempDirName, tdsFileName))

    os.remove(os.path.join(baseDir, tempDirName, tdsFileName.replace('tds', 'twb')))
    utils.createZip(os.path.join(baseDir, tempDirName), os.path.join(baseDir, tdsFileName.replace('tds', 'tdsx')))

    # Clear temp files
    shutil.rmtree(os.path.join(baseDir, tempDirName))
    os.remove(os.path.join(baseDir, tdsFileName.replace('tds', 'twbx')))


def createTwbFromTds(baseDir, tempDirName, twbTemplateFile, tdsFileName, tdeFileName):
    emptywbxmlstr = utils.openfile(twbTemplateFile)
    tdsxmlstr = utils.openfile(os.path.join(baseDir, tdsFileName))

    emptyIntruder = xmlintruder.XmlIntruder(emptywbxmlstr)
    tdsIntruder = xmlintruder.XmlIntruder(tdsxmlstr)

    twbdss = emptyIntruder.subtree('/workbook/datasources/datasource')

    # Store original twb datasource attributes
    attributes = None
    for ds in twbdss:
        attributes = ds.attrib

    # delete twb datasource subtree
    emptyIntruder.delete('/workbook/datasources/datasource')

    # read tds datasource tree
    tdsDatasourceList = tdsIntruder.subtree('/datasource')
    # Change the datasource's attributes with the tds's attributes, and insert into the new twb
    for dse in tdsDatasourceList:
        emptyIntruder.deleteAllAttrib(dse).addAllAttribs(dse, attributes).insertInto('/workbook/datasources', dse)

    # Set the twb path's point to the tde file
    for c in emptyIntruder.subtree('/workbook/datasources/datasource/connection/named-connections/named-connection/connection'):
        emptyIntruder.setAttrib(c, 'dbname', tdeFileName)

    # Set the twb path's point to the tde file
    for c in emptyIntruder.subtree('/workbook/datasources/datasource/extract/connection'):
        emptyIntruder.setAttrib(c, 'dbname', tdeFileName)

    # Save the twb file
    emptyIntruder.write(os.path.join(baseDir, tempDirName, tdsFileName.replace('.tds', '.twb')))

