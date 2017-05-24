# Requirements

The service needs a python install on the host system, also the pip tool.

# Optimizer webservice

This is a flask-based microservice that allows triggering different steps in the optimization pipeline that need to
use Desktop and the injector.


## Basic usage

#### Set up the configuration


First, create a copy of the `service_configuration.py.example` as `service_configuration.py`

```bash
cp service_config.py.example service_config.py
```

Then edit the directories to suit your environment. An example configuration is
provided bellow (this should be the same as the configuration in
`service_config.py`.

```python
# CONFIG --------------------------

# Configuration data for injecting into Tableau Desktop
#
injectorConfig = {

    # The location of "Injector.exe" or "Injector64.exe" depending on your
    # platform and the version of Tableau you are using
    "injector": "c:\\Temp\\Netflix\\programs\\Injector.exe",

    # The Qnject DLL location (this will be injected into Tableau Desktop)
    "dll": "c:\\Temp\\Netflix\\programs\\qnject.dll",

    # Sometimes after launching Tableau, the shell returns an invalid PID,
    # so we try to resolve it with injecting to all running processes with
    # this name (as the service is already bound at this point, subsequest
    # vaccines should not be launched.
    "process-name": "tableau.exe",
}

# Configuration about tableau
tableauConfig = {
    # The path to the Tableau Desktop Executable
    "tableau.exe": "C:\\Program Files\\Tableau\\Tableau 10.2\\bin\\tableau.exe",
}


# Conversion config options
twbConverterConfig = {
    # Where the empty workbook template is located
    "emptyWorkbookTemplate": "c:\\Temp\\Netflix\\template\\emptywb.twb ",
    # Directory where conversion logs are stored
    "logDirectory": 'c:\\Temp\\Netflix\\logs'
}

# Webservice configuration
flaskConfig = {
    # Which port flask should bind to
    "port": 5000,
    # Where to store the uploads
    "uploadDirectory": "c:\\Temp\\Netflix\\uploads",
    # The extensions we allow for  uploading
    "allowedExtensions": set(['tde', 'tds', 'twb', 'twbx', 'tdsx'])
}


# When transfering files using S3, embed your credentials here
s3Config = {
    "bucketName": "",
    "keyId": "",
    "sKeyId": ""
}
```

``` bash
pip install -r requirements.txt

```

#### Start the service
From the client directory start the service:

```bash
python service.py
```

### Web services

``` bash

## Optimize
 - call with local file paths 
 - url: http://localhost:5000/v1/optimize?tds_uri=<file path to .tds>tds&tde_uri=<file path to .tde>
 - example: http://localhost:5000/v1/optimize?tds_uri=c:\Work\Tableau\datasource.tds&tde_uri=c:\Work\Tableau\extractedData.tde

## From S3 links
 - call with s3 file links
 - url: http://localhost:5000/v1/s3?tds_uri=<s3 link to tds file>&tde_uri=<s3 link to tde file>
 - url: http://localhost:5000/v1/s3?tds_uri=https://s3-eu-west-1.amazonaws.com/mybucket/datasource.tds&tde_uri=https://s3-eu-west-1.amazonaws.com/mybucket/extractedData.tde
  
## Upload
 - call with files in the POST request body
 - url: http://localhost:5000/v1/upload
    body params:
      tds_file - <tds file>
      tde_file - <tde file>
  The tde and tds should be sent as file
```

All the service returns a json information about the generated file, like:


``` json
{"ok": 
  {
    "msg": "Created TDSX",
    "downloadLink": "http://1.2.3.4:5000/v1/download/s3_proba1_hliout/proba1.tdsx",
    "file": "c:\\Temp\\Netflix\\uploads\\s3_proba1_hliout\\proba1.tdsx"
  }
}
```

The download link can be called to download the generated tdsx file itself



#### Trigger an optimize

```bash

# Open tableau, load <LOCAL_PATH>, wait for <SLEEP_SECONDS> before injection, then trigger `Optimize`, `Save`, `Exit`
# The input file is overwritten.
curl http://localhost:5000/v1/optimize?sleep=<SLEEP_SECONDS>&file=<LOCAL_PATH>

# Sleep for 10 seconds by default
curl http://localhost:5000/v1/optimize?file=<LOCAL_PATH>
```

Example:

```bash
curl http://localhost:5000/v1/optimize?file=c:\tmp\packaged_tv_2.twbx

# [[{"text": "&Optimize", "result": ["ok"], "address": "0x0000000055930770"}],
#  [{"text": "&Save", "result": ["ok"], "address": "0x000000000E7F0B00"}],
#  [{"text": "E&xit", "result": ["ok"], "address": "0x000000000E7F1180"}]]
```



Note: For now the file to be optimized needs to be present on a locally accessable Windows Path (either local or via windows sharing).




# Command-line interface for triggering menu commands

## Get help

```
➜ ./tde_optimize.py --help
Usage: tde_optimize.py [OPTIONS] [ACTIONS]...

  Connect to a QNjects server injected into Tableau Desktop and runs
  Optimize then Save on a workbook

  The 'ACTIONS' are the actions to search for by text (they will be executed
  in the same order).

  Examples:

  ./env/bin/python tde_optimize.py --help

  ./env/bin/python tde_optimize.py

  ./env/bin/python tde_optimize.py "&Save" --server http://localhost:12345

Options:
  --server TEXT  The QNject server to connect to
  --help         Show this message and exit.

```



# Web services

``` bash

## Optimize
 - call with local file paths
 - url: http://localhost:5000/v1/optimize?tds_uri=<file path to .tds>tds&tde_uri=<file path to .tde>
 - example: http://localhost:5000/v1/optimize?tds_uri=c:\Work\Tableau\datasource.tds&tde_uri=c:\Work\Tableau\extractedData.tde

## From S3 links
 - call with s3 file links
 - url: http://localhost:5000/v1/s3?tds_uri=<s3 link to tds file>&tde_uri=<s3 link to tde file>
 - url: http://localhost:5000/v1/s3?tds_uri=https://s3-eu-west-1.amazonaws.com/mybucket/datasource.tds&tde_uri=https://s3-eu-west-1.amazonaws.com/mybucket/extractedData.tde

## Upload
 - call with files in the POST request body
 - url: http://localhost:5000/v1/upload
    body params:
      tds_file - <tds file>
      tde_file - <tde file>
  The tde and tds should be sent as file
```

All the service returns a json information about the generated file, like:


``` json
{"ok":
  {
    "msg": "Created TDSX",
    "downloadLink": "http://localhost:5000/v1/download/s3_proba1_hliout/proba1.tdsx",
    "file": "c:\\Temp\\Netflix\\uploads\\s3_proba1_hliout\\proba1.tdsx"
  }
}
```

The download link can be called to download the generated tdsx file itself
