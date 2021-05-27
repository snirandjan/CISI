import geopandas as gp
import pytest
from pygeos import to_wkb
from shapely.wkb import loads
from pgpkg import Geopackage


WGS84 = {"init": "epsg:4326"}


def to_shapely(geoms):
    wkb = to_wkb(geoms)
    return wkb.apply(lambda g: loads(g))


def to_gdf(df, crs):
    df = df.copy()
    df["geometry"] = to_shapely(df.geometry)
    return gp.GeoDataFrame(df, crs=crs)


def write_gpkg(filename, df, name, crs):
    with Geopackage(filename, "w") as out:
        out.add_layer(df, name, crs)


@pytest.mark.benchmark(group="write-points")
def test_points_write_benchmark(tmpdir, points_wgs84, benchmark):
    filename = tmpdir / "points_wgs84.gpkg"
    benchmark(write_gpkg, filename, points_wgs84, "points_wgs84", crs="EPSG:4326")


@pytest.mark.benchmark(group="write-points")
def test_points_gp_to_shp_benchmark(tmpdir, points_wgs84, benchmark):
    """Test performance of Geopandas to_file function for shapefiles"""

    filename = str(tmpdir / "points_wgs84.shp")
    df = to_gdf(points_wgs84, crs=WGS84)
    benchmark(df.to_file, filename)


@pytest.mark.benchmark(group="write-points")
def test_points_gp_to_gpkg_benchmark(tmpdir, points_wgs84, benchmark):
    """Test performance of Geopandas to_file function for shapefiles"""

    filename = str(tmpdir / "points_wgs84.gpkg")
    df = to_gdf(points_wgs84, crs=WGS84)
    benchmark(df.to_file, filename, driver="GPKG")


@pytest.mark.benchmark(group="write-lines")
def test_lines_write_benchmark(tmpdir, lines_wgs84, benchmark):
    filename = tmpdir / "lines_wgs84.gpkg"
    benchmark(write_gpkg, filename, lines_wgs84, "lines_wgs84", crs="EPSG:4326")


@pytest.mark.benchmark(group="write-lines")
def test_lines_gp_to_shp_benchmark(tmpdir, lines_wgs84_gdf, benchmark):
    """Test performance of Geopandas to_file function for shapefiles"""

    filename = str(tmpdir / "lines_wgs84.shp")
    benchmark(lines_wgs84_gdf.to_file, filename)


@pytest.mark.benchmark(group="write-lines")
def test_lines_gp_to_gpkg_benchmark(tmpdir, lines_wgs84_gdf, benchmark):
    """Test performance of Geopandas to_file function for shapefiles"""

    filename = str(tmpdir / "lines_wgs84.gpkg")
    benchmark(lines_wgs84_gdf.to_file, filename, driver="GPKG")


@pytest.mark.benchmark(group="write-polygons")
def test_polygons_write_benchmark(tmpdir, polygons_wgs84, benchmark):
    filename = tmpdir / "polygons_wgs84.gpkg"
    benchmark(write_gpkg, filename, polygons_wgs84, "polygons_wgs84", crs="EPSG:4326")


@pytest.mark.benchmark(group="write-polygons")
def test_polygons_gp_to_shp_benchmark(tmpdir, polygons_wgs84_gdf, benchmark):
    """Test performance of Geopandas to_file function for shapefiles"""

    filename = str(tmpdir / "polygons_wgs84.shp")
    benchmark(polygons_wgs84_gdf.to_file, filename)


@pytest.mark.benchmark(group="write-polygons")
def test_polygons_gp_to_gpkg_benchmark(tmpdir, polygons_wgs84_gdf, benchmark):
    """Test performance of Geopandas to_file function for shapefiles"""

    filename = str(tmpdir / "polygons_wgs84.gpkg")
    benchmark(polygons_wgs84_gdf.to_file, filename, driver="GPKG")

