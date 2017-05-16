import json
import time
import os
import sys
import traceback
import subprocess
import re
import utils
from flask import Flask, request
import tableau_file_converter as TableauFileConverter
import tde_optimize

# CONFIG --------------------------

injectorConfig = {
    # "injector-cmd": "Injector64.exe",
    "injector": "c:\\Work\\Git\\xml-intruder-2k\\qinject\\Injector.exe",
    "dll": "c:\\Work\\Git\\xml-intruder-2k\\qinject\\qnject.dll",
    "process-name": "tableau.exe",
}

tableauConfig = {
    "tableau.exe": "C:\\Program Files\\Tableau\\Tableau 10.2\\bin\\tableau.exe",
}

twbConverterConfig = {
    "emptyWorkbookTemplate": 'emptywb.twb',
    "temp": 'twbxTemp',
}

# Pre-configure the qnject handler
baseUrl = "http://localhost:8000/api"
qnjectConfig = tde_optimize.Config(baseUrl=baseUrl)
upload_temp_directory = 'uploads'

valid_extensions = {
    'datasource': ['tde', 'tds', 'tdsx'],
    'workbook': ['twb', 'twbx']
}

# APP ---------------------------


app = Flask(__name__)


def getInjectorCmd(cfg, pid):
    return [cfg["injector"],
            "--process-name", cfg["process-name"],
            "--module-name", cfg["dll"],
            "--inject"]

def getInjectorCmdForPid(cfg, pid):
    return [cfg["injector"],
            "--process-id", str(pid),
            "--module-name", cfg["dll"],
            "--inject"]

# Tries to inject the dll.
def try_injection(cfg, pid, port=8000):
    is_successful = re.compile(r"Successfully injected module")
    result = ""

    # if the proc gives an empty exit code, it will throw, so wrap it
    try:
        cmd = []
        if pid is None:
            cmd = getInjectorCmd(cfg)
        else:
            cmd = getInjectorCmdForPid(cfg, pid)

        print("--> Starting injection using {}".format(cmd))

        # Run the injector
        result = subprocess.check_output(cmd, shell=True)

        if is_successful.search(result):
            print("<-- Injection success into {}".format(pid))
            return {"ok": {"msg": "Succesfully injected", "output": result}}
        else:
            return {"error": {"msg": "Failed injection", "output": result}}

    except subprocess.CalledProcessError as e:
        return {"error": {"msg": "Failed injection", "rc": e.returncode}}


# Launches tableau and returns th POpen object
def launch_tableau_using_popen(tableauExePath, workbookPath, port=8000):
    # Add the vaccine port to the inection stuff
    my_env = os.environ.copy()
    my_env["VACCINE_HTTP_PORT"] = str(port)

    print("Starting Tableau Desktop at '{}' with workbook '{}' with VACCINE_HTTP_PORT={}".format(tableauExePath, workbookPath, my_env["VACCINE_HTTP_PORT"]))
    p = subprocess.Popen([tableauExePath, workbookPath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=my_env)

    # Wait for 0.5s to check the status
    time.sleep(0.5)
    # Check if we succeeded in launching the process
    if p.poll() is not None:
        # raise("Tableau Desktop exited prematurely. Return code:{}".format(p.returncode))
        return {"error": {"msg": "Tableau Desktop exited prematurely. Return code:{}".format(p.returncode),
                          "workbook": workbookPath}}
    else:
        print("Tableau Desktop started with pid {}".format(p.pid))
        return {"ok": {"pid": p.pid, "workbook": workbookPath}}


def start_tableau(cfg, twb, port=8000):
    return launch_tableau_using_popen(cfg["tableau.exe"],  twb, port=port)


# MAKE SURE WE ARE OK AND CAN BE DEBUGGED REMOTELY

@app.route("/")
def root():
    return "TDE Optimizer"


@app.route("/ping")
def ping(): return "pong"


# Get the config for debugging
@app.route("/config")
def get_config():
    return str(json.dumps({"baseUrl": qnjectConfig.baseUrl}))

# GENERATING
# @app.route("/generator", methods=['GET'])
# def generator_help():
#     return json.dumps({"info": {"msg": "Generator services root: use '/generator/start?files=x.tds,x.tde' to start"}})


# TRIGGERING --------------------------

@app.route("/triggers/save")
def trigger_save():
    actions = ["&Optimize", "&Save"]

    # Call the actions
    menu = tde_optimize.get_menu(qnjectConfig)
    return json.dumps(tde_optimize.find_and_trigger_actions(qnjectConfig, actions, menu))


@app.route("/triggers/do-inject")
def trigger_injection():
    return json.dumps(try_injection(injectorConfig, request.args.get('pid', None)))


@app.route("/triggers/start-tableau")
def trigger_open_tableau():
    fn = request.args.get('file', '')
    if fn == "":
        return json.dumps({"error": {"msg": "a 'file' url parameter must be provided."}}), 405
    else:
        return json.dumps(start_tableau(tableauConfig, fn))



def num(s, default=0):
    try:
        return int(s)
    except ValueError:
        return default

################################################################################
# Getting a fresh port for an optimimze run.
# TODO: global bad, but not that bad, we should use some local thingie use some local thingie

# HACK TO GET A VALID PORT FOR THE TABLEAU VACCINES:
# increment it and keep it between a range
vaccinePorts = {
    "i": 0,
    "min": 8000,
    "max": 8999
}

# Gets the next (valid) port for the vaccine
def nextPortIndex(vaccinePorts):
    pmin = vaccinePorts["min"]
    pmax = vaccinePorts["max"]
    nextPort = (vaccinePorts["i"] % (pmax - pmin)) + pmin
    vaccinePorts["i"] = vaccinePorts["i"] + 1
    return nextPort

################################################################################
# Tries to optimize a TWBX using the qnject service.
#
# `twbxPath` : the path to the TWBX file to load and optimize
# returns { "ok": { "file": <OPTIMIZED_PATH> } }
def optimize_wrapper(twbxPath, sleepSeconds=10):

    # Figure out the next port we should use
    port = nextPortIndex(vaccinePorts)

    # Start Tableau Desktop with the file
    print("--> Starting tableau with: {0}".format(twbxPath))
    res = start_tableau(tableauConfig, twbxPath, port=port)

    # Error checking
    if "error" in res:
        return res


    # Waiting for Tableau to start
    pid = res["ok"]["pid"]
    print("--> Tableau Desktop PID: {0}".format(pid))
    print("--> Wating for {0} seconds for Tableau Desktop #{1} to launch".format(sleepSeconds, pid))
    time.sleep(sleepSeconds)

    # Run the injection
    print("--> injecting to {} using port {}".format(pid, port))
    res = try_injection(injectorConfig, pid, port)
    if "error" in res:
        return res

    # Trigger actions
    print("--> Optimize, save and exit")
    actions = ["&Optimize", "&Save", "E&xit"]

    # Call the actions
    injectCfg = tde_optimize.Config(baseUrl="http://localhost:" + str(port) + "/api")
    menu = tde_optimize.get_menu(injectCfg)
    res = tde_optimize.find_and_trigger_actions(injectCfg, actions, menu)
    if "error" in res:
        return res

    # We should be OK at this point
    return {"ok": {"msg": "Triggered actions", "actions": res}}


# Wraps the creation of a combined TDSX file from a TWBX filename
def wrapTwbxToTdsx(fn, twbxDir, tdsFile, tdsxFile):
    res = None
    # call
    try:
        mydir = fn.split(os.path.sep)
        twbxfn = mydir.pop()
        twbxTempDir = os.path.join(os.path.sep.join(mydir), twbxDir)

        return json.dumps({"ok": {
                "msg": "Created TDSX", 
                "file":TableauFileConverter.twbxToTdsx(twbxTempDir, twbxfn, tdsFile, tdsxFile=tdsxFile)
                }}), 200
    except Exception as e:
       
        print(">>> ERROR DURING TDSX CREATION:\n{0}".format( traceback.format_exc()))
        return json.dumps({"error": {"msg": "Error during TWBX to TDSX conversion"}}), 500


################################################################################

# Actual optimize endpoint

@app.route("/optimize")
def trigger_optimize():

    converterConfig = twbConverterConfig

    tde_uri = request.args.get('tde_uri', '').encode('ascii', 'ignore')
    tds_uri = request.args.get('tds_uri', '').encode('ascii', 'ignore')

    # Generate temp directory
    data_path = tds_uri.split(os.path.sep)
    data_path.pop()
    fullTempDir = utils.createTempDirectory(os.path.sep.join(data_path))
    tempDir = fullTempDir.split(os.path.sep).pop()
    # Try the creation of a TWBX from the bits
    try:
        fn = TableauFileConverter.twbxFromTdeAndTds(
                tdeFile=tde_uri,
                tdsFile=tds_uri, 
                baseTwb=converterConfig['emptyWorkbookTemplate'],
                tempDirName=tempDir)
    except:
        return json.dumps({"error": {"msg": "Error during TWBX generation"}}), 500


    # fn = request.args.get('file', '')
    sleepSeconds = num(request.args.get('sleep', '10'), 10)

    if fn == "":
        return json.dumps({"error": {"msg": "a 'file' url parameter must be provided."}}), 500
    else:
        
        res = optimize_wrapper(fn, sleepSeconds=sleepSeconds)
        
        # Error if optimize fails
        if "error" in res:
            return json.dumps(res), 500

        return wrapTwbxToTdsx(fn, twbxDir=tempDir, tdsFile=tds_uri, tdsxFile=tds_uri.split(os.path.sep).pop().replace('tds', 'tdsx'))





# MAIN --------------------------


if __name__ == "__main__":
    app.run(threaded = True)
