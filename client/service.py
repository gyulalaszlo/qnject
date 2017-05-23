import json
import time
import os
import sys
import traceback
import subprocess
import re
import logging
import tempfile
import shutil
from logger_initializer import *
import utils
from flask import Flask, request, redirect, url_for, send_from_directory
import tableau_file_converter as TableauFileConverter
import tde_optimize
from service_config import *
import upload_service as UploadService

# Initialize logger
logging.info("Setting log directory to: " + twbConverterConfig["logDirectory"])
initialize_logger(twbConverterConfig["logDirectory"])


# APP ---------------------------

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = flaskConfig["uploadDirectory"]

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

        logging.info("Starting injection using %s", cmd)

        # Run the injector
        result = subprocess.check_output(cmd, shell=True)

        if is_successful.search(result):
            logging.info("Injection successful into PID=%d", pid)
            return {"ok": {"msg": "Succesfully injected", "output": result}}
        else:
            return {"error": {"msg": "Failed injection", "output": result}}

    except subprocess.CalledProcessError as e:
        return {"error": {"msg": "Failed injection", "rc": e.returncode}}


# Launches tableau and returns th POpen object
def launch_tableau_using_popen(tableauExePath, workbookPath, vaccineLogFile, port=8000 ):
    # Add the vaccine port to the inection stuff
    my_env = os.environ.copy()
    my_env["VACCINE_HTTP_PORT"] = str(port)
    my_env["VACCINE_LOG_FILE"] = vaccineLogFile

    logging.info("Starting Tableau Desktop at '%s' with workbook '%s' with VACCINE_HTTP_PORT=%s", tableauExePath, workbookPath, my_env["VACCINE_HTTP_PORT"])
    p = subprocess.Popen([tableauExePath, workbookPath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=my_env)

    # Wait for 0.5s to check the status
    time.sleep(0.5)
    # Check if we succeeded in launching the process
    if p.poll() is not None:
        # raise("Tableau Desktop exited prematurely. Return code:{}".format(p.returncode))
        return {"error": {"msg": "Tableau Desktop exited prematurely. Return code:{}".format(p.returncode),
                          "workbook": workbookPath}}
    else:
        logging.info("Tableau Desktop started with PID=%d", p.pid)
        return {"ok": {"pid": p.pid, "workbook": workbookPath}}


def start_tableau(cfg, twb, vaccineLogFile, port=8000):
    return launch_tableau_using_popen(cfg["tableau.exe"],  twb, vaccineLogFile, port=port)


# MAKE SURE WE ARE OK AND CAN BE DEBUGGED REMOTELY

@app.route("/")
def root():
    return "TDE Optimizer"



# Get the config for debugging
@app.route("/v1/config")
def get_config():
    return str(json.dumps({"injectorConfig": injectorConfig,
                           "tableauConfig": tableauConfig,
                           "twbConverterConfig": twbConverterConfig}))


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

def nextPortIndex(vaccinePorts):
    """Gets the next (valid) port for the vaccine"""
    pmin = vaccinePorts["min"]
    pmax = vaccinePorts["max"]
    nextPort = (vaccinePorts["i"] % (pmax - pmin)) + pmin
    vaccinePorts["i"] = vaccinePorts["i"] + 1
    return nextPort

################################################################################
def optimize_wrapper(twbxPath, sleepSeconds=10):
    """ Tries to optimize a TWBX using the qnject service.

    `twbxPath` : the path to the TWBX file to load and optimize
     returns { "ok": { "file": <OPTIMIZED_PATH> } }
    """
    logging.info("Starting optimize TWBX for '%s'", twbxPath)

    # Figure out the next port we should use
    port = nextPortIndex(vaccinePorts)

    # Create vaccine log file
    vaccine_log_file = tempfile.TemporaryFile(dir=os.path.join(twbConverterConfig["logDirectory"], 'vaccine_temp'))

    # Start Tableau Desktop with the file
    res = start_tableau(tableauConfig, twbxPath, vaccineLogFile=vaccine_log_file.name, port=port)

    # Error checking
    if "error" in res:
        logging.error("Error while starting Tableau: %s", json.dumps(res))
        return res


    # Waiting for Tableau to start
    pid = res["ok"]["pid"]
    logging.info("Wating for %d seconds for Tableau Desktop PID=%d to launch", sleepSeconds, pid)
    time.sleep(sleepSeconds)

    # Run the injection
    logging.info("Injecting to PID=%d using port %d", pid, port)
    res = try_injection(injectorConfig, pid, port)
    if "error" in res:
        logging.error("Error during injection: %s", json.dumps(res))
        return res

    # Trigger actions
    logging.info("Optimize, save and exit")
    actions = ["&Optimize", "&Save", "E&xit"]

    # Call the actions
    injectCfg = tde_optimize.Config(baseUrl="http://localhost:" + str(port) + "/api")
    menu = tde_optimize.get_menu(injectCfg)
    res = tde_optimize.find_and_trigger_actions(injectCfg, actions, menu)

    # TODO
    # Create vaccine log for the process
    # vaccine_log_file[0].close()

    if os.path.isfile(vaccine_log_file.name):
        logging.info('Vaccine: ' + vaccine_log_file.name + ' to ' + os.path.join(twbConverterConfig["logDirectory"], 'vaccine_' + str(pid) + '.log'))
        os.system ("copy %s %s" % (vaccine_log_file.name, os.path.join(twbConverterConfig["logDirectory"], 'vaccine_' + str(pid) + '.log')))
        # shutil.copy(vaccine_log_file.name, os.path.join(os.getcwd(), twbConverterConfig["logDirectory"], 'vaccine_' + str(pid) + '.log'))
    else:
        logging.info('Vaccine temp log file already deleted')


    if "error" in res:
        logging.error("Error during menu triggers: %s", json.dumps(res))
        return res

    # We should be OK at this point
    return {"ok": {"msg": "Triggered actions", "actions": res}}



def wrapTwbxToTdsx(baseDir, tempDirName, tdsFileName):
    """Wraps the creation of a combined TDSX file from a TWBX filename"""
    logging.info("Starting to generate TDSX from '%s'", os.path.join(baseDir, tdsFileName.replace('tds', 'twbx')))
    # call
    try:
        (fileUri, downloadLink) = TableauFileConverter.twbxToTdsx(baseDir, tempDirName, tdsFileName, downloadUrlBase='http://localhost:5000/v1/download/')

        return json.dumps({"ok": {
                "msg": "Created TDSX",
                "file": fileUri,
                "downloadLink": downloadLink
                }}), 200
    except Exception as e:
        logging.error("Error during TDSX creation: %s", traceback.format_exc())
        return json.dumps({"error": {"msg": "Error during TWBX to TDSX conversion"}}), 500



################################################################################


def requires_query_argument(name):
    arg = request.args.get(name, None)
    if arg is None:
        return ({"msg": "a '" + name + "' url parameter must be provided."}, None)
    else:
        return (None,arg.encode('ascii', 'ignore').strip())



################################################################################

# S3 Endpoint
@app.route('/v1/s3', methods=['GET'])
def from_s3():
    logging.info("S3 service called.")

    (tds_uri_error, tds_uri) = requires_query_argument('tds_uri')
    (tde_uri_error, tde_uri) = requires_query_argument('tde_uri')

    if tde_uri_error is not None or tds_uri_error is not None:
        return json.dumps({"error": {"msg": "Missing required arguments", "results":[tds_uri_error, tde_uri_error]}})

    tds_file_name = tds_uri.split('/').pop().strip()
    tde_file_name = tde_uri.split('/').pop().strip()

    # Generate temporary directory for the uploaded file
    (tempFull, tempName) = utils.createTempDirectory(flaskConfig["uploadDirectory"], prefix=utils.getPrefix(tds_file_name, type='s3'))

    # save tds, tde file from s3 link
    logging.info("Download " + tds_file_name + " from S3")
    tds_file_url = UploadService.s3_download_file(s3Config["bucketName"], tds_uri, os.path.join(tempFull, tds_file_name))
    logging.info("Download " + tde_file_name + " from S3")
    tde_file_url = UploadService.s3_download_file(s3Config["bucketName"], tde_uri, os.path.join(tempFull, tde_file_name))

    logging.info("Download finished.")

    logging.info("Triggering optimize service")
    return redirect(url_for('.trigger_optimize',\
        tds_uri=os.path.join(tempFull, tds_file_name),\
        tde_uri=os.path.join(tempFull, tde_file_name)))



# File upload endpoint
@app.route('/v1/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        # tde_file, tds_file

        if 'tde_file' not in request.files:
            logging.error("Error during upload: No tde_file given in request body.")
            return json.dumps({"error": {"msg": "Upload error: No tde_file given in request body."}})
        if 'tds_file' not in request.files:
            logging.error("Error during upload: No tds_file given in request body.")
            return json.dumps({"error": {"msg": "Upload error: No tds_file given in request body."}})

        tde_file = request.files['tde_file'].strip()
        tds_file = request.files['tds_file'].strip()
        # if user does not select file, browser also
        # submit a empty part without filename
        if tde_file.filename == '':
            logging.error("Error during upload: No selected tde_file.")
            return json.dumps({"error": {"msg": "Upload error: selected tde_file."}})
        if tds_file.filename == '':
            logging.error("Error during upload: No selected tds_file.")
            return json.dumps({"error": {"msg": "Upload error: selected tds_file."}})

        # Generate temporary directory for the uploaded file
        (tempFull, tempName) = utils.createTempDirectory(app.config['UPLOAD_FOLDER'], prefix=utils.getPrefix(tds_file.filename, type='upolad'))

        # if file and UploadService.allowed_file(file.filename):
        if tds_file:
            tds_filename = tds_file.filename.encode('ascii', 'ignore')
            tds_file.save(os.path.join(tempFull, tds_filename))

        if tde_file:
            tde_filename = tde_file.filename.encode('ascii', 'ignore')
            tde_file.save(os.path.join(tempFull, tde_filename))

            # We should trigger the optimizer here passing the local paths
            test_url = url_for('.trigger_optimize',\
                tds_uri=os.path.join(tempFull, tds_filename),\
                tde_uri=os.path.join(tempFull, tde_filename))
            return redirect(test_url)
            # return 'Arrived files'
    return 


#Download finished tdsx by link
@app.route("/v1/download/<path:filename>", methods=['GET'])
def download(filename):
    if filename is None:
        return json.dumps({"error": {"msg": "Download file path is missing"}})

    (path, dlFile) = utils.getDownloadLink(filename, app.config['UPLOAD_FOLDER'])
    return send_from_directory(path, dlFile, as_attachment=False)



# Actual optimize endpoint
@app.route("/v1/optimize")
def trigger_optimize():
    """ Optimizes a pair of Tableau Workbook and Datasource files.


    Usage:
        GET /v1/optimize?tde_uri=<TDE_FILE>&tds_uri=<TDS_FILE>
        -> 200 OK => {"ok": { "msg": "Created TDSX", "file":<OUTPUT_TDSX_PATH> }}

        GET /v1/optimize?tde_uri=<TDE_FILE>&tds_uri=<TDS_FILE>
        -> 500 ERROR => {"error": { "msg": <REASON>, <...ERROR_METADATA> }}

    Required parameters:

        - tde_uri: full local path of the TDE file to use as base
        - tds_uri: full local path of the TDS file describing the datasource and the calculations

            """
    ########################################

    (tde_uri_error, tde_uri) = requires_query_argument('tde_uri')
    (tds_uri_error, tds_uri) = requires_query_argument('tds_uri')

    if tde_uri_error is not None or tds_uri_error is not None:
        return json.dumps({"error": {"msg": "Missing required arguments", "results":[tds_uri_error, tde_uri_error]}})

    ########################################

    converterConfig = twbConverterConfig
    file_info = {}

    ########################################

    # Generate temp directory
    full_base_dir = os.path.dirname(tds_uri)
    tds_file_name = os.path.basename(tds_uri)
    tde_file_name = os.path.basename(tde_uri)
    
    (tempFull, tempName) = utils.createTempDirectory(full_base_dir)

    ########################################

    # Try the creation of a TWBX from the bits
    try:
        fn = TableauFileConverter.twbxFromTdeAndTds(
                baseDir=full_base_dir,
                tempDirName=tempName,
                tdeFileName=tde_file_name,
                tdsFileName=tds_file_name,
                baseTwb=converterConfig['emptyWorkbookTemplate'])
    except Exception:
        logging.error("Error during TWBX creation: %s", traceback.format_exc())
        return json.dumps({"error": {"msg": "Error during TWBX generation"}}), 500

    ########################################
    logging.info('Optimizer input twbx saved to %s', fn)
    file_info['start'] = utils.getZipFileInfo(fn)

    # Sleep till we load the TDE (or do we)
    sleepSeconds = num(request.args.get('sleep', '10'), 10)

    # Create vaccine here pass to optimize_wrapper
    res = optimize_wrapper(fn, sleepSeconds=sleepSeconds)
    file_info['optimized'] = utils.getZipFileInfo(fn)

    logging.info(json.dumps(file_info, indent=4, sort_keys=False))

    if "error" in res:
        return json.dumps(res), 500

    return wrapTwbxToTdsx(full_base_dir, tempName, tds_file_name)


# MAIN --------------------------


if __name__ == "__main__":
    app.run(threaded = True)
