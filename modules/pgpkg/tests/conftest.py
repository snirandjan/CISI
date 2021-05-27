from geopandas import GeoDataFrame
import numpy as np
from numpy import random
from pandas import DataFrame
import pygeos as pg
from pytest import fixture
from shapely.geometry import Point, LineString, Polygon


def generate_lon_lat(size):
    """Generate arrays of longitude, latitude.

    Parameters
    ----------
    size : int
        length of arrays to generate

    Returns
    -------
    list of 2 arrays
    """

    return [random.sample(size) * 360 - 180, random.sample(size) * 179 - 90]


@fixture
def points_wgs84():
    size = 1000
    x, y = generate_lon_lat(size)

    # generate some other fields in the data frame
    i = random.randint(-32767, 32767, size=size)
    ui = random.randint(0, 65535, size=size).astype("uint64")

    df = DataFrame(data={"x": x, "y": y, "i": i, "ui": ui, "labels": i.astype("str")})
    df["geometry"] = pg.points(np.array([x, y]).T)

    return df


@fixture
def lines_wgs84():
    size = 1000
    line_length = 10  # number of vertices
    # generate some fields in the data frame
    f = random.sample(size) * 360 - 180
    i = random.randint(-32767, 32767, size=size)
    ui = random.randint(0, 65535, size=size).astype("uint64")

    df = DataFrame(data={"f": f, "i": i, "ui": ui, "labels": i.astype("str")})
    df["geometry"] = df.apply(
        lambda x: pg.linestrings(np.array(generate_lon_lat(line_length)).T), axis=1
    )

    return df


@fixture
def polygons_wgs84():
    size = 1000
    x1, y1 = generate_lon_lat(size)
    x2, y2 = generate_lon_lat(size)

    # generate some fields in the data frame
    f = random.sample(size) * 360 - 180
    i = random.randint(-32767, 32767, size=size)
    ui = random.randint(0, 65535, size=size).astype("uint64")

    df = DataFrame(
        data={
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "f": f,
            "i": i,
            "ui": ui,
            "labels": i.astype("str"),
        }
    )

    # Generate random triangles
    df["geometry"] = df[["x1", "y1", "x2", "y2"]].apply(
        lambda row: pg.polygons(
            [[row.x1, row.y1], [row.x2, row.y1], [row.x2, row.y2], [row.x1, row.y1]]
        ),
        axis=1,
    )

    return df


### Shapely geometry objects & GeoDataFrames
@fixture
def points_wgs84_gdf():
    size = 1000
    x, y = generate_lon_lat(size)

    # generate some other fields in the data frame
    i = random.randint(-32767, 32767, size=size)
    ui = random.randint(0, 65535, size=size).astype("uint64")

    df = DataFrame(data={"x": x, "y": y, "i": i, "ui": ui, "labels": i.astype("str")})
    return GeoDataFrame(
        df, geometry=df[["x", "y"]].apply(Point, axis=1), crs={"init": "EPSG:4326"}
    )


@fixture
def lines_wgs84_gdf():
    size = 1000
    line_length = 10  # number of vertices
    # generate some fields in the data frame
    f = random.sample(size) * 360 - 180
    i = random.randint(-32767, 32767, size=size)
    ui = random.randint(0, 65535, size=size).astype("uint64")

    df = DataFrame(data={"f": f, "i": i, "ui": ui, "labels": i.astype("str")})

    # Generate random lines
    geometry = df.apply(
        lambda x: LineString(np.column_stack(generate_lon_lat(line_length))), axis=1
    )
    return GeoDataFrame(df, geometry=geometry, crs={"init": "EPSG:4326"})


@fixture
def polygons_wgs84_gdf():
    size = 1000
    x1, y1 = generate_lon_lat(size)
    x2, y2 = generate_lon_lat(size)

    # generate some fields in the data frame
    f = random.sample(size) * 360 - 180
    i = random.randint(-32767, 32767, size=size)
    ui = random.randint(0, 65535, size=size).astype("uint64")

    df = DataFrame(
        data={
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "f": f,
            "i": i,
            "ui": ui,
            "labels": i.astype("str"),
        }
    )

    # Generate random triangles
    geometry = df[["x1", "y1", "x2", "y2"]].apply(
        lambda row: Polygon(
            [[row.x1, row.y1], [row.x2, row.y1], [row.x2, row.y2], [row.x1, row.y1]]
        ),
        axis=1,
    )
    return GeoDataFrame(df, geometry=geometry, crs={"init": "EPSG:4326"})
