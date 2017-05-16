import os
import zipfile
import requests
import xmlintruder


def openfile(path):
    text = ''
    if not os.path.isfile(path):
        raise Exception("File not found: {path}".format(path=path))
    with open(path, 'r') as xml_file:
        text = xml_file.read()
    xml_file.close()
    return text

def unzip(source_filename, dest_dir):
    with zipfile.ZipFile(source_filename) as zf:
        zf.extractall(dest_dir)

def deleteall(path):
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
    wd = os.getcwd()
    foo = zipfile.ZipFile(dest, 'w')
    os.chdir(src)
    for root, dirs, files in os.walk('.'):
        for f in files:
            print(f)
            foo.write(os.path.join(root, f))

    foo.close()
    os.chdir(wd)

def callHttpGet(twbxPath, twbxFileName):
    params = {'file': os.path.join(twbxPath, twbxFileName)}

    print('Calling: http://localhost:5000/optimize?file=' + params.get('file') )
    response = requests.get('http://localhost:5000/optimize', params=params)
    return response