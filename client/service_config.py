# CONFIG --------------------------

injectorConfig = {
    # "injector-cmd": "Injector64.exe",
    "injector": "Injector.exe",
    "dll": "qnject.dll",
    "process-name": "tableau.exe",
}

tableauConfig = {
    "tableau.exe": "C:\\Program Files\\Tableau\\Tableau 10.2\\bin\\tableau.exe",
}

twbConverterConfig = {
    "emptyWorkbookTemplate": "emptywb.twb",
    "logDirectory": 'logs'
}

flaskConfig = {
    "uploadDirectory": "uploads",
    "allowedExtensions": set(['tde', 'tds', 'twb', 'twbx', 'tdsx'])
}

s3Config = {
    "bucketName": "",
    "keyId": "",
    "sKeyId": ""
}