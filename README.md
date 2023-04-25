# Integration of modelled traffic speed in openrouteservice

Analysis and evaluation of using different traffic speed data sets in route planning using openrouteservice.

## Dependencies

- Python >= 3.10
- poetry >=1.3.2
- docker

## Preparation

### 1. Set up Python environment

Make sure you have poetry and a python version >= 3.10 installed.

To install the dependencies, run:

```
$ poetry install
```

To activate the environment, run poetry shell or run every python command with `poetry run python ...`.

### 2. Create Google Routing API key

Create a Google Routing API key. Copy the `sample.env` file and name it `.env`. Instert your Google Routing API key.


## Usage

First generate Google and ORS routes, then analyze them and in the end plot the statistics as boxenplots. Follow these steps to run the analysis:

### 1. Generate Google routes

**Important:** A valid Google API key needs to be provided in `./.env`. Be careful not to exceed the free limits to avoid costs.

``


### 2. Generate ORS routes

The script `./src/scripts/generate_ors_routes.py` generates a ORS route for each Google route. Before running the script the respective ORS docker instance must be started.

Pre-generated Google routes are available on heibox. Download the city folder in the `data` folder and move it to `./data/` of this project (there should be a txt-file).

#### A. Start ORS docker containers

The ORS instances can be run using docker-compose files. They are on heibox located in the `./ors` directory. Cites available so far: Berlin, Nairobi and Cincinnati.

If you want to run the scripts for a different city, you need to change the docker containers accordingly. Check "Run for different cities with different traffic data" below for more information.

Start a container by executing:

```
$ cd ./ors/ORS TYPE/openrouteservice/docker
$ docker compose up -d
```

**Note:**: Running all of containers at the same time won't work because they need a lot of RAM.

Check if the ORS is ready by opening `http://localhost:8080/ors/health` in your browser (may take a minute). If it says `ready`, it is ready to receive the request in step 2 (this may take a few minutes). Below is a list of the ORS instances:

| Name         | URL | Description                                     |
|--------------|-----|-------------------------------------------------|
| normal       | http://localhost:8080/ors/health | ORS without traffic data |
| modelled_mean | http://localhost:8081/ors/health | ORS with modelled mean traffic speed |
| modelled_p50 | http://localhost:8082/ors/health | ORS with modelled 50th percentile traffic speed |
| modelled_p85 | http://localhost:8083/ors/health | ORS with modelled 85th percentile traffic speed |
| uber_p85     | http://localhost:8084/ors/health | ORS with uber 85th percentile traffic speed |

#### B. Run the script

Run the script to generate ORS routes while the relevant ORS container is running:
```
$ poetry run python ./src/scripts/generate_ors_routes.py -h

usage: generate_ors_routes.py [-h] -t ORS type -c City name [-d Data directory] [-s splits count]

Generate ORS routes

options:
  -h, --help          show this help message and exit
  -t ORS type         Type of ORS. Check Readme for more information.
  -c City name        City name. Check Readme for more information.
  -d data directory   Directory with route data, default: 'data'
  -s splits count     Google route splits, default = 10
```

This script needs to be run for all ORS instances with different traffic speed data.
```
poetry run python ./src/scripts/generate_ors_routes.py -c berlin -t normal
poetry run python ./src/scripts/generate_ors_routes.py -c berlin -t modelled_mean
poetry run python ./src/scripts/generate_ors_routes.py -c berlin -t modelled_p50
poetry run python ./src/scripts/generate_ors_routes.py -c berlin -t modelled_p85
poetry run python ./src/scripts/generate_ors_routes.py -c berlin -t uber_p85
```

#### C. Run for different cities with different traffic data

1. Copy your pbf file to `./ors/ORS TYPE/openrouteservice/docker/data/`.
2. Adapt path of pbf file in docker-compose.yml

    Open the `docker-compose.yml` file in `./ors/ORS TYPE/openrouteservice/docker/` and set the `OSM_FILE` variable to your pbf file name, e.g.
    ```
    OSM_FILE: ./docker/data/nairobi.osm.pbf
    ```
3. Copy traffic speed data csv file to: `./ors/ORS TYPE/openrouteservice/openrouteservice/src/main/files/uber_traffic/`.

    **Important:** Rename the file to `modelled_traffic_speed.csv`
4. If it exists, delete the `graphs` folder in `./ors/ORS TYPE/openrouteservice/docker/`.
5. If you want to run it again with different traffic data/pbf files, rebuild the image when composing with `docker compose up -d --build`
6. Follow steps 1 "Start ORS docker containers" and 2 "Run the script"

### 3. Analyze routes

The script `./src/scripts/route_analysis.py` calculates statistics to compare the ORS routes to the according Google routes.

After generating all routes in the steps above, run the analysis with:
```
$ poetry run python ./src/scripts/route_analysis.py -h

usage: route_analysis.py [-h] -c City name

Analyzes routes and calculates statistics

options:
  -h, --help    show this help message and exit
  -c City name  City name. Check Readme for more information.
```

### 4. Plot statistics

To generate Boxenplots with the statistics, run the Jupyter Notebook `./src/scripts/notebooks/Boxenplots.ipynb`.

If running for multiple cities, specify the city name in the global variable `CITY` at the top of the notebook.

The generated plots are saved to disk in `./data/CITY/export/figures/`.

## Help

If you encounter an error that a port cannot be accessed in step 2 when building docker images, make sure it is free on your system. If you have run jupyter notebooks beforehand (especially when doing the analysis again for different cities), restart the jupyter kernel to free up the port.

## Authors

- Christina Ludwig
- Nikolaos Kolaxidis

## License

This project is licensed under the MIT License - see the LICENSE file for details

## Acknowledgments
