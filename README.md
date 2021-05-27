# Critical Infrastructure Spatial Index (CISI)
This repository provides the code to:
- extract critical infrastructure assets from OSM data
- estimate the amount of infrastructure for given grid cells
- calculate the Critical Infrastructure System Index (CISI)

It also provides a Jupyter Notebook and additional code to reproduce the figures and supplementary material in Nirandjan et al. (in progress).

## Data requirements
- All critical infrastructure data is based on OpenStreetMap (OSM), which can be freely downloaded. The planet file used in Nirandjan et al. (in progress) is downloaded at January 8, 2021. However, the latest release of planet.osm.pbf file can be used to run the code.
- Gridded global population distribution data is available from the WorldPop data portal (https://www.worldpop.org). In Nirandjan et al. (in progress), global population distribution data of 2020 is used. 
- Gridded global GDP data is avaiable from https://datadryad.org/stash/dataset/doi:10.5061/dryad.dk1j0

## Python requirements

Recommended option is to use a [miniconda](https://conda.io/miniconda.html)
environment to work in for this project, relying on conda to handle some of the
trickier library dependencies.

```bash

# Add conda-forge channel for extra packages
conda config --add channels conda-forge

# Create a conda environment for the project and install packages
conda env create -f environment.yml
conda activate CoInf

```

**Requirements:** [NumPy](http://www.numpy.org/), [pandas](https://pandas.pydata.org/), [geopandas](http://geopandas.org/), [matplotlib](https://matplotlib.org/), [pygeos](https://pypi.org/project/pygeos/)

## How to cite
If you use the CISI in your work, please cite the corresponding paper:

Nirandjan, S., Koks, E.E., Ward, P.J., Aerts, J.C.J.H. (in progress). A spatially-explicit harmonized global dataset of critical infrastructure. 


    @article{koks2019_gmtra,
      title={A spatially-explicit harmonized global dataset of critical infrastructure},
      author={Nirandjan, S., Koks, E.E., Ward, P.J. and Aerts, J.C.J.H. },
      journal={...},
      volume={...},
      number={...},
      pages={...},
      year={...},
      publisher={...}
    }

### License
Copyright (C) 2021 Sadhana Nirandjan & Elco Koks. All versions released under the [MIT license](LICENSE).
