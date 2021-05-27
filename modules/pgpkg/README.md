# Pygeos <=> Geopackage I/O

[![Build Status](https://travis-ci.org/brendan-ward/pgpkg.svg?branch=master)](https://travis-ci.org/brendan-ward/pgpkg)
[![Coverage Status](https://coveralls.io/repos/github/brendan-ward/pgpkg/badge.svg?branch=master)](https://coveralls.io/github/brendan-ward/pgpkg?branch=master)

Faster I/O between [`pygeos`](https://github.com/pygeos/pygeos) and [geopackage](https://www.geopackage.org/) file format for use in GIS.

Geopackages are a modern, sqlite-based file format containing geospatial data. These are intended to overcome shortcomings in the shapefile format that is ubiquitous in the geospatial data world.

`pygeos` is a very fast Python wrapper around the GEOS library. It provides very fast geospatial operations on geometries, including checking for intersections between geometries or calculating the geometric intersection between them.

The goal of this library is to allow serializing `pandas` DataFrames containing `pygeos` geometry objects as fast as possible. We wanted faster GIS compatible outputs from our processing chains in other projects, which are starting to leverage `pygeos` heavily.

This is a shim until `pygeos` is fully integrated into `geopandas`.

## Installation

Not available on PyPi yet, so clone the repository in Github and `python setup.py develop`.

This requires the latest available version for `pygeos`, right now from the `master` branch of that repository.

## Usage

To create a geopackage, given a pandas DataFrame `df` containing `pygeos` geometry objects in the 'geometry' column:

```
from pgpkg import Geopackage

with Geopackage('test.gpkg', 'w') as out:
  out.add_layer(df, name='Test', crs='EPSG:4326')
```

Note: only write mode is supported at this time.

## Early results:

According to the benchmarks in our test suite, we are seeing 2-3x speedups compared to writing shapefiles or geopackages in `geopandas`.

## WARNING

This package may change radically once `pygeos` is used internally within `geopandas`.

We are not focusing on full coverage of all of the different ways of writing data to a geopackage. If that is what you need, use `ogr2ogr` or one of the other Python packages available for geopackages.
