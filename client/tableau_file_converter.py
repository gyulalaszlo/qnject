import os
import shutil
from lxml import etree

import utils
import xmlintruder

def twbxFromTdeAndTds(tdeFile, tdsFile, baseTwb='emptywb.twb', tempDirName='twbxTemp'):
    # Get dir
    # for now same directory fro tde and tds, anyway copy to one dir
    # craete temp for twbx
    working_directory_store = os.getcwd()
    # full_dir = os.path.join(tdeFile.split(os.path.sep).pop()).join(os.path.sep)
    full_dir_list = tdeFile.split(os.path.sep)
    full_dir_list.pop()
    full_dir = os.path.sep.join(full_dir_list)

    # change wd
    os.chdir(full_dir)

    # create temp dir
    if not os.path.exists(tempDirName):
        os.mkdir(tempDirName)

    # os.mkdir(tempDirName)
    # generate

    # Copy to twb temp directory
    shutil.copy(tdeFile, os.path.join(full_dir, tempDirName))

    # Manipulate the temp and save to the twb temp dir
    new_twb_name = tdsFile.split(os.path.sep).pop().replace('.tds', '.twb')

    createTwbFromTds( baseTwb, tdsFile, os.path.join(tempDirName, new_twb_name), tdeFile)       

    # Step x: Creat te twbx from twb + tde
    twbxName = tdsFile.split(os.path.sep).pop().replace('.tds', '.twbx')
    utils.createZip(os.path.join(full_dir, tempDirName), tdsFile.split(os.path.sep).pop().replace('.tds', '.twbx'))

    # return path
    os.chdir(working_directory_store)
    return os.path.join(full_dir, twbxName)

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
    
    return os.path.join(twbxDir, twbxFileName)



def twbxToTdsx(twbxDir, twbxFileName, tdsxTempDir='tdsxTemp', tdsxFile='lookat.tdsx'):
    # remove all file from twbx temp directory
    utils.deleteall(twbxDir)

    # extract twbx to twbxTemp dir
    utils.unzip(twbxFileName, twbxDir)

    # get tde file
    # copy the original tds to this dir
    tdsfiles = utils.getFiles(tdsxTempDir)
    tdsfile = None
    for tf in tdsfiles:
        if tf.get('name').endswith('tds'):
            # Copy to twb temp directory
            shutil.copy(tf.get('full'), twbxDir)
            tdsfile = tf

    # find twb file from the twbx
    twbfiles = utils.getFiles(twbxDir)
    twbfile = None
    for tf in twbfiles:
        if tf.get('name').endswith('twb'):
            twbfile = tf

    # copy twb database subtree back to the original tds file
    tdsxmlstr = utils.openfile(tdsfile.get('full'))
    twbxmlstr = utils.openfile(twbfile.get('full'))
    
    tdsIntruder = xmlintruder.XmlIntruder(tdsxmlstr)
    twbIntruder = xmlintruder.XmlIntruder(twbxmlstr)

    # get tds datasource
    tdsDatasourceList = tdsIntruder.subtree('/datasource')

    # Store original twb datasource attributes
    attributes = None
    for ds in tdsDatasourceList:
        attributes = ds.attrib

    # Delete tds datasource
    # tdsIntruder.gettree() = etree.Element()

    # read tds datasource tree
    twbDatasourceList = twbIntruder.subtree('/workbook/datasources/datasource')

    # copy twb datasource tag attributes with the tds attributes
    for twbds in twbDatasourceList:
        twbIntruder.deleteAllAttrib(twbds).addAllAttribs(twbds, attributes).insertInto('/workbook/datasources', twbds)
        tdsIntruder.settree(etree.tostring(twbds))

    tdsIntruder.write(os.path.join(twbxDir, tdsfile.get('name')))

    os.remove(twbfile.get('full'))
    utils.createZip(twbxDir, tdsxFile)


def createTwbFromTds(twb, tds, path, tde):
    emptywbxmlstr = utils.openfile(twb)
    tdsxmlstr = utils.openfile(tds)

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
        emptyIntruder.setAttrib(c, 'dbname', tde.split(os.path.sep).pop())

    # Set the twb path's point to the tde file
    for c in emptyIntruder.subtree('/workbook/datasources/datasource/extract/connection'):
        emptyIntruder.setAttrib(c, 'dbname', tde.split(os.path.sep).pop())

    # Save the tdsx file
    emptyIntruder.write(path)

