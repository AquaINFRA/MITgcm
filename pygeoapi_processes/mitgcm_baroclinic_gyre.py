# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Francesco Martinelli <francesco.martinelli@ingv.it>
#
# Copyright (c) 2022 Tom Kralidis
# Copyright (c) 2024 Francesco Martinelli
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import logging
import os
import json
import shutil
import subprocess

'''
curl -X POST "http://localhost:5001/processes/hello-mitgcm-params/execution" -H "Content-Type: application/json" -d "{\"inputs\":{ \"endTime\": \"24000\", \"deltaT\": \"2400\", \"viscAh\": \"5000\"}}"
'''

from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError
import pygeoapi.process.catalunya.gluemncbig_adapted as gluemncbig_adapted
import pygeoapi.process.catalunya.gendata_adapted as gendata_adapted

LOGGER = logging.getLogger(__name__)
#: Process metadata and description
PROCESS_METADATA = {
    'version': '0.2.0',
    'id': 'mitgcm-baroclinic-gyre',
    'title': {
        'en': 'MITgcm Baroclinic Gyre Tutorial'
    },
    'description': {
        'en': 'Run the Baroclinic Gyre Tutorial of the MITgcm and play with some parameters. The results can be downloaded after the simulation finishes. You can call this function using any HTTP Client. Using curl, the an example call would be like this: `curl -X POST "http://195.148.30.163/pygeoapi/processes/mitgcm-baroclinic-gyre/execution" -H "Content-Type: application/json" -d "{\"inputs\":{ \"endTime\": \"24000\", \"deltaT\": \"2400\", \"viscAh\": \"5000\"}}"`.'
    },
    'jobControlOptions': ['sync-execute', 'async-execute'],
    'keywords': ['AquaINFRA', 'catalunya use case', 'MITgcm', 'Baroclinic Gyre'],
    'links': [{
        'type': 'text/html',
        'rel': 'about',
        'title': 'information',
        'href': 'https://mitgcm.readthedocs.io/en/latest/examples/baroclinic_gyre/baroclinic_gyre.html',
        'hreflang': 'en-US'
    }],
    'inputs': {
        'endTime': {
            'title': 'Duration of the simulation',
            'description': 'The duration of the simulation (parameter \"endTime\") in seconds. Defaults to 12000 seconds, i.e. 200 minutes.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['endTime', 'mitgcm', 'AquaINFRA', 'catalunya use case']
        },
        'deltaT': {
           'title': 'Timestep of the simulation',
            'description': 'Timestep of the simulation (parameter \"deltaT\") in seconds. Defaults to 1200 seconds, i.e. 20 minutes.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['deltaT', 'mitgcm', 'AquaINFRA', 'catalunya use case']
        },
        'viscAh': {
            'title': 'Horizontal viscosity',
            'description': 'Horizontal viscosity (parameter \"viscAh\") of the model in m^2/s. Defaults to 5000 m^2/s.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['viscAh', 'mitgcm', 'AquaINFRA', 'catalunya use case']
        },
        'tauMax': {
            'title': 'Zonal wind-stress',
            'description': 'Wind stress maximum (parameter \"tauMax\"), i.e. the tangential force that the wind provides against the ocean surface, in N/m^2. For example, 0.0 means no wind, while 0.9 is a hurricane. Defaults to 0.1 N/m^2.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['tauMax', 'gendata', 'mitgcm', 'AquaINFRA', 'catalunya use case']
        },
        'Tmin': {
            'title': 'Minimum temperature of Ocean Surface',
            'description': 'Minimum temperature of Ocean Surface (parameter \"Tmin\"), in degrees Celsius, Defaults to 0 degrees Celsius.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['Tmin', 'gendata', 'mitgcm', 'AquaINFRA', 'catalunya use case']
        },
        'Tmax': {
            'title': 'Maximum temperature of Ocean Surface',
            'description': 'Maximum temperature of Ocean Surface (parameter \"Tmax\"), in degrees Celsius, Defaults to 30 degrees Celsius.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['Tmax', 'gendata', 'mitgcm', 'AquaINFRA', 'catalunya use case']
        }
    },
    'outputs': {
        'grid': {
            'title': 'Merged grid*.nc files',
            'description': 'Merged grid*.nc files, as one netcdf file',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        },
        'state': {
            'title': 'Merged state*.nc files',
            'description': 'Merged state*.nc files, as one netcdf file',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        },
        'stdout': {
            'title': 'Model output',
            'description': 'The output that the model writes to stdout, as text file.',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        }
    },
    'example': {
        'inputs': {
            'endTime': '12000',
            'deltaT': '1200',
            'viscAh': '5000',
            'tauMax': '0.1',
            'Tmin': '0.0',
            'Tmax': '30.0'
        }
    }
}

class MitgcmBaroclinicGyreProcessor(BaseProcessor):

    def __init__(self, processor_def):
        super().__init__(processor_def, PROCESS_METADATA)
        self.supports_outputs = True
        self.job_id = 'dummy_job_id' # why is this not set? Too old version of pygeoapi?
        self.config = None

        # TODO: Find a way to not hardcode these (i.e. write into config):
        self.path_to_fortran_dir     = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/build'
        self.path_to_run_cwd         = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run'
        #self.path_to_input_file_data = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run/data'
        self.path_to_input_file_data = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run/data_backup_20240917'
        self.path_to_gendata_outputs = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/input/'
        self.path_to_result_netcdf   = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run/mnc_test_0001'

        # Set config:
        config_file_path = os.environ.get('MITGCM_CONFIG_FILE', "./config.json")

        with open(config_file_path, 'r') as config_file:
            self.config = json.load(config_file)

        with open(config_file_path, 'r') as config_file:
            self.config = json.load(config_file)

    def __repr__(self):
        return f'<MitgcmBaroclinicGyreProcessor> {self.name}'

    def set_job_id(self, job_id: str):
        self.job_id = job_id

    def execute(self, data, outputs=None):
        # User inputs
        endTime = int(data.get('endTime', '12000'))
        deltaT = int(data.get('deltaT', '1200'))
        viscAh = int(data.get('viscAh', '5000'))
        tauMax = float(data.get('tauMax', '0.1'))
        Tmin = float(data.get('Tmin', '0.0'))
        Tmax = float(data.get('Tmax', '30.0'))


        ###################################################
        ### Rewrite "data" input file                   ###
        ### with new values for endTime, deltaT, viscAh ###
        ###################################################

        # Write a new "data" input file!
        # TODO: Not hardcode paths!
        LOGGER.error('###################################################################################################')
        LOGGER.error('Starting to rewrite run/data')
        #input_file_data = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run/data'
        input_file_data_old = self.path_to_input_file_data
        input_file_data_to_be_used = self.path_to_input_file_data.replace('data_backup_20240917', 'data')
        input_file_data_new = input_file_data_to_be_used.rstrip('/')+'_new'

        with open(input_file_data_old, 'r') as oldfile:
            with open(input_file_data_new, 'w') as newfile:
                for line in oldfile:

                    if line.strip().startswith('endTime'):
                        LOGGER.error('Prev... %s' % line)
                        line = ' endTime=%s.,\n' % endTime
                        LOGGER.error('Setting %s' % line)
                        # TODO: Ask about the dot??
                    elif line.strip().startswith('deltaT'):
                        LOGGER.error('Prev... %s' % line)
                        line = ' deltaT=%s.,\n' % deltaT
                        LOGGER.error('Setting %s' % line)
                    elif line.strip().startswith('viscAh'):
                        LOGGER.error('Prev... %s' % line)
                        line = ' viscAh=%s.,\n' % viscAh
                        LOGGER.error('Setting %s' % line)

                    newfile.write(line)

        shutil.copy(input_file_data_new, input_file_data_to_be_used)

        ###################################################
        ### Create new binary input data, using gendata ###
        ### with new values for tauMax, Tmin, Tmax      ###
        ###################################################

        # Note: The names of the files are defined in:
        # https://github.com/MITgcm/MITgcm/blob/master/verification/tutorial_baroclinic_gyre/input/data

        LOGGER.error('###################################################################################################')
        LOGGER.error('### Calling gendata...')
        #out_path = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/input/'
        out_path = self.path_to_gendata_outputs
        gendata_adapted.gendata(LOGGER=LOGGER, out_path=out_path, tauMax=tauMax, Tmin=Tmin, Tmax=Tmax)
        LOGGER.error('### Calling gendata... done')
        LOGGER.error('###################################################################################################')

        ###########################
        ### Run fortran program ###
        ###########################
        # TODO: Not hardcode path to compiled fortran program
        program_name = 'mitgcmuv'
        #path_fortran = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/build'
        path_fortran = self.path_to_fortran_dir
        path_cwd = self.path_to_run_cwd
        exit_code, err_msg, stdout = call_fortran_script(LOGGER, program_name, path_fortran, path_cwd)

        if not exit_code == 0:
            raise ProcessorExecuteError(user_msg="FORTRAN script failed with exit code %s" % exit_code)

        #####################
        ### Treat results ###
        #####################

        # Store stdout:
        downloadfilename_stdout = 'outputs-stdout-%s-%s.txt' % (self.metadata['id'], self.job_id)
        downloadfilepath_stdout = self.config['download_dir']+downloadfilename_stdout
        with open(downloadfilepath_stdout, 'w') as outfile:
            outfile.write(stdout)

        # Make result file names for netcdf files:
        downloadfilename_grid = 'outputs-grid-%s-%s.nc' % (self.metadata['id'], self.job_id)
        downloadfilepath_grid = self.config['download_dir']+downloadfilename_grid
        downloadfilename_state = 'outputs-state-%s-%s.nc' % (self.metadata['id'], self.job_id)
        downloadfilepath_state = self.config['download_dir']+downloadfilename_state

        # Create download link:
        downloadlink_grid = self.config['download_url'].rstrip('/')+os.sep + downloadfilename_grid
        downloadlink_state = self.config['download_url'].rstrip('/')+os.sep + downloadfilename_state
        downloadlink_stdout = self.config['download_url'].rstrip('/')+os.sep + downloadfilename_stdout

        ############################################
        ### Glue netcdf results using gluemncbig ###
        ############################################

        # Where to find result netcdf files:
        #result_path = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run/mnc_test_0001'
        result_path = self.path_to_result_netcdf
        grid_files = []
        state_files = []
        for filename in os.listdir(result_path):
            if not filename.endswith('.nc'):
                LOGGER.error('Ignoring: %s' % filename)
            elif filename == 'state.nc':
                # From previous glueings... They lead to errors!
                LOGGER.error('Ignoring: %s' % filename)
            elif filename == 'grid.nc':
                # From previous glueings... They lead to errors!
                LOGGER.error('Ignoring: %s' % filename)
            elif filename.startswith('grid'):
                grid_files.append(result_path+'/'+filename)
                LOGGER.error('Grid file:  %s' % filename)
            elif filename.startswith('state'):
                state_files.append(result_path+'/'+filename)
                LOGGER.error('State file: %s' % filename)

        LOGGER.error('All state files: %s' % state_files)
        LOGGER.error('All grid files:  %s' % grid_files)

        # Glue files together using gluemncbig
        netcdf_version = 1
        gluemncbig_adapted.glue(downloadfilepath_grid, grid_files, netcdf_version)
        gluemncbig_adapted.glue(downloadfilepath_state, state_files, netcdf_version)


        ######################
        ### Log and return ###
        ######################

        # Log:
        LOGGER.error('Written text output to: %s' % downloadfilepath_stdout)
        LOGGER.error('Written glued grid*.nc to: %s' % downloadfilepath_grid)
        LOGGER.error('Written glued state*.nc to: %s' % downloadfilepath_state)
        LOGGER.error('Text output downloadable at: %s' % downloadlink_stdout)
        LOGGER.error('Glued grid*.nc downloadable at: %s' % downloadlink_grid)
        LOGGER.error('Glued state*.nc downloadable at: %s' % downloadlink_state)

        # Return links to two files to user
        response_object = {
            "outputs": {
                "message": "Job finished, here are the links to your results.",
                "grid": {
                    "title": PROCESS_METADATA["outputs"]["grid"]["title"],
                    "description": PROCESS_METADATA["outputs"]["grid"]["description"],
                    "href": downloadlink_grid
                },
                "state": {
                        "title": PROCESS_METADATA["outputs"]["state"]["title"],
                        "description": PROCESS_METADATA["outputs"]["state"]["description"],
                        "href": downloadlink_state
                },
                "stdout": {
                        "title": PROCESS_METADATA["outputs"]["stdout"]["title"],
                        "description": PROCESS_METADATA["outputs"]["stdout"]["description"],
                        "href": downloadlink_stdout
                }
            }
        }

        LOGGER.error('This will be the response: %s' % response_object)

        return 'application/json', response_object



def call_fortran_script(LOGGER, program_name, path_fortran, path_cwd):
    # TODO: Currently all log messages are ERROR because the dev pygeoapi only writes ERROR messages...

    LOGGER.error('Now calling bash which calls fortran: %s' % program_name)
    fortran_file = path_fortran.rstrip('/')+os.sep+program_name
    cmd = [fortran_file]

    # We need to set cwd!
    # TODO: Not hardcode path!
    #mycwd = '/TODO/path/to/mitgcm/MITgcm/verification/tutorial_baroclinic_gyre/run'
    mycwd = path_cwd

    LOGGER.error('Command: %s' % cmd)
    LOGGER.error('Running command... (Output will be shown once finished)')
    p = subprocess.Popen(cmd, cwd=mycwd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutdata, stderrdata = p.communicate()
    LOGGER.error("Done running command! Exit code from bash: %s" % p.returncode)

    # Print stdout and stderr
    stdouttext = stdoutdata.decode()
    stderrtext = stderrdata.decode()
    if len(stderrdata) > 0:
        err_and_out = 'FORTRAN stdout and stderr:\n___PROCESS OUTPUT {name} ___\n___stdout___\n{stdout}\n___stderr___\n{stderr}\n___END PROCESS OUTPUT {name} ___\n______________________'.format(
            name=program_name, stdout=stdouttext, stderr=stderrtext)
        LOGGER.error(err_and_out)
    else:
        err_and_out = 'FORTRAN stdout:\n___PROCESS OUTPUT {name} ___\n___stdout___\n{stdout}\n___stderr___\n___(Nothing written to stderr)___\n___END PROCESS OUTPUT {name} ___\n______________________'.format(
            name=program_name, stdout=stdouttext)
        LOGGER.info(err_and_out)
    return p.returncode, err_and_out, stdouttext
