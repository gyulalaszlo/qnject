# CONFIG --------------------------

injectorConfig = {
    # "injector-cmd": "Injector64.exe",
    "injector": "c:\\Temp\\Netflix\\programs\\Injector.exe",
    "dll": "c:\\Temp\\Netflix\\programs\\qnject.dll",
    "process-name": "tableau.exe",
}

tableauConfig = {
    "tableau.exe": "C:\\Program Files\\Tableau\\Tableau 10.2\\bin\\tableau.exe",
}

twbConverterConfig = {
    "emptyWorkbookTemplate": "c:\\Temp\\Netflix\\template\\emptywb.twb ",
    "logDirectory": 'c:\\Temp\\Netflix\\logs'
}

flaskConfig = {
    "uploadDirectory": "c:\\Temp\\Netflix\\uploads",
    "allowedExtensions": set(['tde', 'tds', 'twb', 'twbx', 'tdsx'])
}

s3Config = {
    "bucketName": "",
    "keyId": "",
    "sKeyId": ""
}