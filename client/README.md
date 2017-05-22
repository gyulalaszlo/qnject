# Optimizer webservice

This is a flask-based microservice that allows triggering different steps in the optimization pipeline that need to
use Desktop and the injector.


## Basic usage

#### Set up the configuration

Currently the configuration for the steps is stored in the microservice python file itself:

```python

# Configuration for the QNject bits
injectorConfig = {
    # Path to the Injector executable for the target architecture
    "injector": "C:\\tmp\\_builds\\qnject64\\Injector64.exe",
    # Path to the QNject dll for the target architecture
    "dll": "c:\\tmp\\_builds\\qnject64\\vaccine\\Release\\qnject.dll",
    # The process name we want to hook.
    "process-name": "tableau.exe",
}

# Configuration for launching Tableau
tableauConfig = {
    # The path to the tableau.exe executable
    "tableau.exe": "C:\\Program Files\\Tableau\\Tableau 10.2\\bin\\tableau.exe",
}

# The
baseUrl = "http://localhost:8000/api"
```

TODO: move the config to a separate file


#### Start the service

```bash
python service.py
```

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
 - call with loacl file paths 
 - url: http://localhost:5000/v1/optimize?tds_uri=<file path to .tds>tds&tde_uri=<file path to .tde>

## From S3 links
 - call with s3 file links
 - url: http://localhost:5000/v1/s3?tds_uri=<aws link to file>&tde_uri=<aws link to file>
  
## Upload
 - call with files in the POST request body
 - url: http://localhost:5000/v1/upload
    body params:
      tds_file - <tds file>
      tde_file - <tde file>
  The tde and tds should be sent as file parameter
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

