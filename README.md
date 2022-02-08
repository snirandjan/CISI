# Critical Infrastructure Spatial Index (CISI)
This repository provides the code to:
- extract critical infrastructure assets from OSM data
- estimate the amount of infrastructure for given grid cells
- calculate the Critical Infrastructure Spatial Index (CISI)

It also provides a Jupyter Notebook and additional code to reproduce the figures and supplementary material in Nirandjan et al. (2022).

## Data requirements
- All critical infrastructure data is based on OpenStreetMap (OSM), which can be freely downloaded. The planet file used in Nirandjan et al. (2022) is downloaded at January 8, 2021. However, the latest release of planet.osm.pbf file can be used to run the code.
- Gridded global population distribution data is available from the WorldPop data portal (https://www.worldpop.org). In Nirandjan et al. (2022), global population distribution data of 2020 is used. 
- Gridded global GDP data is avaiable from https://datadryad.org/stash/dataset/doi:10.5061/dryad.dk1j0. In Nirandjan et al. (2022), we use the GDP_PPP_30arcsec file for 2015.

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


    @article{Nirandjan2022_CISI,
      title={A spatially-explicit harmonized global dataset of critical infrastructure},
      author={Nirandjan, S., Koks, E.E., Ward, P.J. and Aerts, J.C.J.H. },
      journal={Scientific Data},
      volume={...},
      number={...},
      pages={...},
      year={2022},
      publisher={...}
    }
    
The following DOI can be cited for this repository:
[![DOI](https://zenodo.org/badge/327351993.svg)](https://zenodo.org/badge/latestdoi/327351993)

## Global CISI visualizer
The CISI and the sub-score per system is visualized at a global scale via https://cisi-index.appspot.com/. This is only done for a resolution of 0.25 degrees for speed performance considerations. Have a look and discover where critical infrastructure is located!  

### License
Copyright (C) 2021 Sadhana Nirandjan & Elco Koks. All versions released under the [MIT license](LICENSE).
