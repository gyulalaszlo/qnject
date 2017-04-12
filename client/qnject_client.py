"""QNject CLient.

Usage:
  qnject_client.py list [--server=<server> --log=<loglevel>]
  qnject_client.py find-by <PREDICATE> [--server=<server> --log=<loglevel>]
  qnject_client.py --version
  qnject_client.py (-h | --help)
  qnject_client.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
import string

import sys
from docopt import docopt
import requests
import logging
import string


# PATHS ----------------------------------------


def path(config, subpaths):
    return config["server"] + "/".join([config["api_base"]] + subpaths)

# Creates configuration data for the qnject grabber
def config_from(server, api_base="api", logLevel="INFO"):
    logger = getLogger("qnject", logLevel)
    logger.info("Creating config.")
    return { "server": server,
             "api_base": api_base,
             "logger": logger}

# BASE -------------------------------------------

def get_path(config, path_bits):
    log = config["logger"]
    reqPath = path(config, path_bits)
    log.info("Getting: '%s'", reqPath)

    r = requests.get(reqPath)

    log.info("Status is: %d", r.status_code)

    return r.json()

# PREDICATES -------------------------------------------


def compile_predicate(log, str):
    try:
        method_body = "def compiled_qnject_predicate(o):\n  " + "\n  ".join(string.split(str, "\n"))
        cpl = compile(method_body, 'compiled_qnject_predicate', 'exec')
        exec(cpl)
        compiled_qnject_predicate("hello")

    except:
        log.error("Error during predicate compilation: %s", sys.exc_info()[0])
        raise







# GETTERS ----------------------------------------


def list_all_objects(config):
    r = get_path(config, ["qwidgets"])
    return r["widgets"]



def find_objects_matching(config, predicate):
    return filter(predicate, list_all_objects(config))




# BASIC PREDICATES ----------------------------

def has_no_object_name(o):
    return o["objectName"] == ""



# MAIN ----------------------------------------


# Sets the log level from the command line arg
def getLogger(name,lvl):

    # assuming loglevel is bound to the string value obtained from the
    # command line argument. Convert to upper case to allow the user to
    # specify --log=DEBUG or --log=debug
    numeric_level = getattr(logging, lvl.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % lvl)

    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(numeric_level)

    return logger



if __name__ == '__main__':
    args = docopt(__doc__, version="Qnject Client 0.2")
    # Create the config
    config = config_from(server=args.get("--server", "http://localhost:8000"),
                         logLevel=args.get("--log", "INFO")
                         )
    config["logger"].info("Server is: %s", config["server"])


    print args
    if args["list"]:
        print find_objects_matching(config, has_no_object_name)

    elif args["find-by"]:
        compile_predicate(config["logger"], args.get("<PREDICATE>", "return true"))
        print "FIND-by", args



