# MITgcm as an OGC processing service (AquaINFRA project)

## What is the AquaINFRA project?

Read here: https://aquainfra.eu/

## What are OGC processes?

... TODO Write or find a quick introduction ...

Read here: https://ogcapi.ogc.org/

## WHat is pygeoapi?

...TODO...

Read here: https://pygeoapi.io/

## Steps to deploy this as OGC processes

Note: The steps below are work in progress and may not be complete. If you test this and notice it does not work, please contact Merret Buurman at IGB Berlin - we are grateful for any advice for improvement!!

* Have the model itself compiled and running, in `/.../path/to/MITgcm/verification/tutorial_baroclinic_gyre/`
* Add the process python file here: `/.../pygeoapi/pygeoapi/process/catalunya/mitgcm_baroclinic_gyre.py`
* Add the adapted `gendata_adapted.py` file here: `/.../pygeoapi/pygeoapi/process/catalunya/gendata_adapted.py`
* Add the adapted `gluemncbig_adapted.py` file here: `/.../pygeoapi/pygeoapi/process/catalunya/gluemncbig_adapted.py`
* Deploy an instance of pygeoapi (https://pygeoapi.io/). We will assume it is running on `localhost:5000`.
* Go to the `process` directory of your installation, i.e. `cd /.../pygeoapi/pygeoapi/process`.
* Clone this repo and checkout this branch
* Open the `plugin.py` file (`vi /.../pygeoapi/pygeoapi/plugin.py`) and add these lines to the `'process'` section:

```
    ...
    'process': {
        'HelloWorld': 'pygeoapi.process.hello_world.HelloWorldProcessor',
        'MitgcmBaroclinicGyre': 'pygeoapi.process.catalunya.mitgcm_baroclinic_gyre.MitgcmBaroclinicGyreProcessor'
        ...
    },
    ...
```

* Open the `pygeoapi-config.yaml` file (`vi /.../pygeoapi/pygeoapi-config.yaml`) and add these lines to the `resources` section:

```
resources:
    ...

    mitgcm-baroclinic-gyre:
        type: process
        processor:
            name: MitgcmBaroclinicGyre

    ...
```

* Config file: Make sure you have a `config.json` sitting either in pygeoapi's current working dir (`...TODO...`) or in an arbitrary path that pygeoapi can find through the environment variable `MITGCM_CONFIG_FILE`.
* When running with flask or starlette, you can add that env var by adding the line `os.environ['MITGCM_CONFIG_FILE'] = '/.../config.json'` to `/.../pygeoapi/pygeoapi/starlette_app.py`
* Make sure this config file contains:

```
{
	...
	TODO INSERT MORE ONCE STUFF IS NO LONGER HARDCODED!
	"download_dir": "/.../",
	"download_url": "http://www.bla.com/download/",
    ...
}
```

* Downloading of results:
** If you don't need this right now, just put any writeable path into `download_dir`, where you want the results to be written. Put some dummy value into `download_url`.
** If you want users to be able to download results from remote, have some webserver running (e.g. `nginx` or `apache2`) that you can use to serve static files. The directory for the static results and the URL where that is reachable have to be written into `download_dir` and `download_url`.
* Make sure to create a directory for inputs, add the required inputs to there, and write it into `input_path` of the config file:

```
INSERT REQUIRED INPUTS - ANY YET?
```

* Install the following python packages: `numpy` (TODO: any others?)
* Start pygeoapi following their documentation
* Now you should be able to call the processes using any HTTP client, for example curl. Example requests can be found on top of the process python files (e.g. `mitgcm_baroclinic_gyre.py`).
* For an example process, call:


```
curl -X POST "http://localhost:5000/processes/mitgcm-baroclinic-gyre/execution" -H "Content-Type: application/json" -d "{\"inputs\":{ \"endTime\": \"24000\", \"deltaT\": \"2400\", \"viscAh\": \"5000\"}}"

# More beautiful:
curl -x POST --location 'http://localhost:5000/processes/mitgcm-baroclinic-gyre/execution' \
--header 'Content-Type: application/json' \
--data '{
    "inputs": {
        "endTime": "24000",
        "deltaT": "2400",
        "viscAh": "5000"
    }
}'

```


