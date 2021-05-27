import os

import geopandas as gp
import pytest

from pgpkg import Geopackage, to_gpkg


def write_gpkg(filename, df, name, crs):
    with Geopackage(filename, "w") as out:
        out.add_layer(df, name, crs)


def test_points_write(tmpdir, points_wgs84):
    filename = tmpdir / "points_wgs84.gpkg"

    with Geopackage(filename, "w") as out:
        out.add_layer(points_wgs84, "points_wgs84", crs="EPSG:4326")

    assert os.path.exists(filename)

    # TODO: verify written properly


def test_points_write_no_index(tmpdir, points_wgs84):
    filename = tmpdir / "points_wgs84.gpkg"

    with Geopackage(filename, "w") as out:
        out.add_layer(points_wgs84, "points_wgs84", crs="EPSG:4326", index=False)

    assert os.path.exists(filename)

    # TODO: verify written properly


def test_points_write_func(tmpdir, points_wgs84):
    filename = tmpdir / "points_wgs84.gpkg"

    to_gpkg(points_wgs84, filename, name="points_wgs84", crs="EPSG:4326")
    assert os.path.exists(filename)

    # TODO: verify written properly


def test_points_write_func_no_index(tmpdir, points_wgs84):
    filename = tmpdir / "points_wgs84.gpkg"

    to_gpkg(points_wgs84, filename, name="points_wgs84", crs="EPSG:4326", index=False)
    assert os.path.exists(filename)


def test_points_write_func_no_name(tmpdir, points_wgs84):
    filename = tmpdir / "points_wgs84.gpkg"

    to_gpkg(points_wgs84, filename, crs="EPSG:4326")
    assert os.path.exists(filename)


def test_lines_write(tmpdir, lines_wgs84):
    filename = tmpdir / "lines_wgs84.gpkg"

    with Geopackage(filename, "w") as out:
        out.add_layer(lines_wgs84, "lines_wgs84", crs="EPSG:4326")

    assert os.path.exists(filename)

    # TODO: verify written properly
    # verify includes geometry bounds


def test_polygons_write(tmpdir, polygons_wgs84):
    filename = tmpdir / "polygons_wgs84.gpkg"

    with Geopackage(filename, "w") as out:
        out.add_layer(polygons_wgs84, "polygons_wgs84", crs="EPSG:4326")

    assert os.path.exists(filename)

    # TODO: verify written properly
    # verify includes geometry bounds


def test_write_missing_ext(tmpdir, points_wgs84):
    filename = tmpdir / "points_wgs84"

    with Geopackage(filename, "w") as out:
        out.add_layer(points_wgs84, "points_wgs84", crs="EPSG:4326")

    assert os.path.exists("{}.gpkg".format(filename))
