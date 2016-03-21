#!/usr/bin/env python

"""
    A dcmtk style storescu application. 
    
    Used as an SCU for sending DICOM objects from
"""

import argparse
import logging
import os
import socket
import sys

from pydicom import read_file
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian, \
    ExplicitVRBigEndian

from pynetdicom import AE
from pynetdicom import StorageSOPClassList

logger = logging.Logger('storescu')
stream_logger = logging.StreamHandler()
formatter = logging.Formatter('%(levelname).1s: %(message)s')
stream_logger.setFormatter(formatter)
logger.addHandler(stream_logger)
logger.setLevel(logging.ERROR)

def _setup_argparser():
    # Description
    parser = argparse.ArgumentParser(
        description="The storescu application implements a Service Class User "
                    "(SCU) for the Storage Service Class. For each DICOM "
                    "file on the command line it sends a C-STORE message to a  "
                    "Storage Service Class Provider (SCP) and waits for a "
                    "response. The application can be used to transmit DICOM "
                    "images and other composite objectes.", 
        usage="storescu [options] peer port")
        
    # Parameters
    req_opts = parser.add_argument_group('Parameters')
    req_opts.add_argument("peer", help="hostname of DICOM peer", type=str)
    req_opts.add_argument("port", help="TCP/IP port number of peer", type=int)
    req_opts.add_argument("dcmfile_in", 
                          metavar="dcmfile-in",
                          help="DICOM file or directory to be transmitted", 
                          type=str)

    # General Options
    gen_opts = parser.add_argument_group('General Options')
    gen_opts.add_argument("--version", 
                          help="print version information and exit", 
                          action="store_true")
    gen_opts.add_argument("--arguments", 
                          help="print expanded command line arguments", 
                          action="store_true")
    gen_opts.add_argument("-q", "--quiet", 
                          help="quiet mode, print no warnings and errors", 
                          action="store_true")
    gen_opts.add_argument("-v", "--verbose", 
                          help="verbose mode, print processing details", 
                          action="store_true")
    gen_opts.add_argument("-d", "--debug", 
                          help="debug mode, print debug information", 
                          action="store_true")
    gen_opts.add_argument("-ll", "--log-level", metavar='[l]', 
                          help="use level l for the logger (fatal, error, warn, "
                               "info, debug, trace)", 
                          type=str, 
                          choices=['fatal', 'error', 'warn', 
                                   'info', 'debug', 'trace'])
    gen_opts.add_argument("-lc", "--log-config", metavar='[f]', 
                          help="use config file f for the logger", 
                          type=str)

    # Network Options
    net_opts = parser.add_argument_group('Network Options')
    net_opts.add_argument("-aet", "--calling-aet", metavar='[a]etitle', 
                          help="set my calling AE title (default: STORESCU)", 
                          type=str, 
                          default='STORESCU')
    net_opts.add_argument("-aec", "--called-aet", metavar='[a]etitle', 
                          help="set called AE title of peer (default: ANY-SCP)", 
                          type=str, 
                          default='ANY-SCP')

    return parser.parse_args()

args = _setup_argparser()

if args.verbose:
    logger.setLevel(logging.INFO)
    pynetdicom_logger = logging.getLogger('pynetdicom')
    pynetdicom_logger.setLevel(logging.INFO)
    
if args.debug:
    logger.setLevel(logging.DEBUG)
    pynetdicom_logger = logging.getLogger('pynetdicom')
    pynetdicom_logger.setLevel(logging.DEBUG)

logger.debug('$storescu.py v%s %s $' %('0.1.0', '2016-02-10'))
logger.debug('')

# Check file exists and is readable and DICOM
logger.debug('Checking input files')
try:
    f = open(args.dcmfile_in, 'rb')
    dataset = read_file(f, force=True)
    f.close()
except IOError:
    logger.error('Cannot read input file %s' %args.dcmfile_in)
    sys.exit()
except:
    logger.error('File may not be DICOM %s' %args.dcmfile_in)
    sys.exit()

# Set Transfer Syntax options
transfer_syntax = [ImplicitVRLittleEndian,
                   ExplicitVRLittleEndian,
                   ExplicitVRBigEndian]

# Bind to port 0, OS will pick an available port
ae = AE(ae_title=args.calling_aet,
        port=0,
        scu_sop_class=StorageSOPClassList,
        scp_sop_class=[],
        transfer_syntax=transfer_syntax)

# Request association with remote
assoc = ae.associate(args.peer, args.port, args.called_aet)

if assoc.is_established:
    logger.info('Sending file: %s' %args.dcmfile_in)
    
    status = assoc.send_c_store(dataset)
    
    assoc.Release()


# Quit
ae.quit()


