import os
import zipfile
import requests
from datetime import datetime
import logging
import tzlocal
import xmlintruder
import tempfile


def openfile(path):
    logging.info('Opening file: ' + path)
    text = ''
    if not os.path.isfile(path):
        raise Exception("File not found: {path}".format(path=path))
    with open(path, 'r') as xml_file:
        text = xml_file.read()
    xml_file.close()
    return text

def unzip(source_filename, dest_dir):
    logging.info('Extracting file: ' + source_filename + ' to ' + dest_dir)
    with zipfile.ZipFile(source_filename) as zf:
        zf.extractall(dest_dir)

def deleteall(path):
    logging.info('Deleting directory: ' + path)
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

def getFiles(path):
    result = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            result.append({
                'path': root,
                'name': name,
                'full': os.path.join(root, name)
            })
    return result
    

def createZip(src, dest):
    logging.info('Creating pack from ' + src + ' to ' + dest)
    foo = zipfile.ZipFile(dest, 'w')
    for root, dirs, files in os.walk(src):
        for f in files:
            logging.info('\tAdding file: ' + os.path.join(root, f))
            foo.write(os.path.join(root, f), f)

    foo.close()

def callHttpGet(twbxPath, twbxFileName):
    params = {'file': os.path.join(twbxPath, twbxFileName)}

    logging.info('Calling: http://localhost:5000/optimize?file=' + params.get('file') )
    response = requests.get('http://localhost:5000/optimize', params=params)
    return response

# Creates a temporary directory in path, and return only the name of it without the path
def createTempDirectory(path):
    fullTempDir = tempfile.mkdtemp(dir=path)
    logging.info('Creating temporary directory: ' + fullTempDir)
    return fullTempDir.split(os.path.sep).pop()


# Convert the unix timestamp ("seconds since epoch") to the local time
def getTimeString(stamp):
    unix_timestamp = float(stamp)
    local_timezone = tzlocal.get_localzone() # get pytz timezone
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
    return local_time.strftime("%Y-%m-%d %H:%M:%S.%f%z (%Z)")


# Return the file info string
# file name(size) - modified
def getFileInfo(filePath, callback):
    stat = os.stat(filePath)
    name = filePath.split(os.path.sep).pop()
    sizeInByte = stat[ST_SIZE]
    atime = stat[ST_ATIME]
    mtime = stat[ST_MTIME]
    ctime = stat[ST_CTIME]
    return name + '(' + sizeInByte + '): ' + getTimeString(atime) + ', '\
        + getTimeString(mtime) + ', '\
        + getTimeString(mtime)

