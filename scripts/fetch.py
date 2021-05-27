import os
import geopandas
import pandas
import ogr
import numpy 
from osgeo import gdal
from tqdm import tqdm
from shapely.wkb import loads

gdal.SetConfigOption("OSM_CONFIG_FILE", os.path.join("..","osmconf.ini"))

def landuse(osm_path):
    """
    Function to extract land-use polygons from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)
                       
    sql_lyr = data.ExecuteSQL("SELECT osm_id,landuse from multipolygons where landuse is not null")

    osm_data = []
    if data is not None:
        for feature in sql_lyr:
            try:
                if feature.GetField('landuse') is not None:
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    data_type=feature.GetField('landuse')
                    osm_id = feature.GetField('osm_id')
    
                    osm_data.append([osm_id,data_type,shapely_geo])
            except:
                print("WARNING: skipped landuse shape")                       
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(osm_data) > 0:
        return geopandas.GeoDataFrame(osm_data,columns=['osm_id','landuse','geometry'],
                                crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No landuse shapes or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','landuse','geometry'],crs={'init': 'epsg:4326'})

    
def buildings(osm_path):
    """
    Function to extract building polygons from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique building polygons.
    
    """
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    buildings=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,amenity,building from multipolygons where building is not null")
        for feature in sql_lyr:
            try:
                if feature.GetField('building') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    building=feature.GetField('building')
                    amenity=feature.GetField('amenity')

                    buildings.append([osm_id,building,amenity,shapely_geo])
            except:
                    print("WARNING: skipped building")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(buildings) > 0:
        return geopandas.GeoDataFrame(buildings,columns=['osm_id','building','amenity','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','building','amenity','geometry'],crs={'init': 'epsg:4326'})


def roads(osm_path):
    """
    Function to extract road linestrings from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique road linestrings.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    roads=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,highway FROM lines WHERE highway IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('highway') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    highway=feature.GetField('highway')
                    roads.append([osm_id,highway,shapely_geo])
            except:
                    print("WARNING: skipped a road")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(roads) > 0:
        return geopandas.GeoDataFrame(roads,columns=['osm_id','highway','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','highway','geometry'],crs={'init': 'epsg:4326'})
    
def railway(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    railways=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,service,railway FROM lines WHERE railway IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('railway') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    railway=feature.GetField('railway')
                    railways.append([osm_id,railway,shapely_geo])
            except:
                    print("warning: skipped railway")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(railways) > 0:
        return geopandas.GeoDataFrame(railways,columns=['osm_id','railway','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','railway','geometry'],crs={'init': 'epsg:4326'})

def railway_hubs(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    railways_hubs=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,service,railway FROM points WHERE railway IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('railway') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    railway=feature.GetField('railway')
                    railways_hubs.append([osm_id,railway,shapely_geo])
            except:
                    print("warning: skipped railway")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(railways_hubs) > 0:
        return geopandas.GeoDataFrame(railways_hubs,columns=['osm_id','railway','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','railway','geometry'],crs={'init': 'epsg:4326'})    
    
def railway_stations(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    railways_hubs=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,service,railway FROM multipolygon WHERE railway IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('railway') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    railway=feature.GetField('railway')
                    railways_hubs.append([osm_id,railway,shapely_geo])
            except:
                    print("warning: skipped railway")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(railways_hubs) > 0:
        return geopandas.GeoDataFrame(railways_hubs,columns=['osm_id','railway','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','railway','geometry'],crs={'init': 'epsg:4326'})  
    

def electricity(osm_path):
    """
    Function to extract electricity linestrings from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    powerlines=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,voltage,power FROM lines WHERE power IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('power') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    powerline=feature.GetField('power')
                    voltage=feature.GetField('voltage')

                    powerlines.append([osm_id,powerline,voltage,shapely_geo])
            except:
                    print("warning: skipped power line")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(powerlines) > 0:
        return geopandas.GeoDataFrame(powerlines,columns=['osm_id','powerline','voltage','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','powerline','voltage','geometry'],crs={'init': 'epsg:4326'})
    
def electricity_nodes(osm_path):
    """
    Function to extract electricity points from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    powerpoints=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,voltage,power FROM points WHERE power IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('power') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    powerpoint=feature.GetField('power')
                    voltage=feature.GetField('voltage')

                    powerpoints.append([osm_id,powerpoint,voltage,shapely_geo])
            except:
                    print("warning: skipped power points")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(powerpoints) > 0:
        return geopandas.GeoDataFrame(powerpoints,columns=['osm_id','powerpoint','voltage','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','powerpoint','voltage','geometry'],crs={'init': 'epsg:4326'})
    
def electricity_areas(osm_path):
    """
    Function to extract electricity multipolygons from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    
    """
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    powerareas=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,voltage,power FROM multipolygons WHERE power IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('power') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    powerarea=feature.GetField('power')
                    voltage=feature.GetField('voltage')

                    powerareas.append([osm_id,powerarea,voltage,shapely_geo])
            except:
                    print("warning: skipped power areas")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(powerareas) > 0:
        return geopandas.GeoDataFrame(powerareas,columns=['osm_id','powerarea','voltage','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','powerarea','voltage','geometry'],crs={'init': 'epsg:4326'})
        
def aeroway(osm_path):
    """
    Function to extract aeroway multipolygons from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique aeroway polygons.
    
    """    
    
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)    
    
    air_structures=[]        
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id, aeroway FROM multipolygons WHERE aeroway IS NOT NULL")
        for feature in sql_lyr:
            try:
                if feature.GetField('aeroway') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    aeroway=feature.GetField('aeroway')

                    air_structures.append([osm_id,aeroway,shapely_geo])
            except:
                    print("warning: skipped aeroway")
    
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")
    
    if len(air_structures) > 0:
        return geopandas.GeoDataFrame(air_structures,columns=['osm_id','aeroway','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No aeroway stuctures or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','aeroway','geometry'],crs={'init': 'epsg:4326'})
    
def amenity(osm_path):
    """
    Function to extract amenity polygons from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique building polygons.
    
    """
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    amenities=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,building,amenity from multipolygons where amenity is not null")
        for feature in sql_lyr:
            try:
                if feature.GetField('amenity') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    building=feature.GetField('building')
                    amenity=feature.GetField('amenity')

                    amenities.append([osm_id,amenity,building,shapely_geo])
            except:
                    print("WARNING: skipped amenity")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(amenities) > 0:
        return geopandas.GeoDataFrame(amenities,columns=['osm_id','amenity','building','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','amenity','building','geometry'],crs={'init': 'epsg:4326'})
    
def man_made(osm_path):
    """
    Function to extract building polygons from OpenStreetMap
    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique building polygons.
    
    """
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    man_mades=[]    
    if data is not None:
        sql_lyr = data.ExecuteSQL("SELECT osm_id,man_made from multipolygons where man_made is not null")
        for feature in sql_lyr:
            try:
                if feature.GetField('man_made') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkb()) 
                    if shapely_geo is None:
                        continue
                    man_made=feature.GetField('man_made')

                    man_mades.append([osm_id,man_made,shapely_geo])
            except:
                    print("WARNING: skipped man_made")
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    

    if len(man_mades) > 0:
        return geopandas.GeoDataFrame(man_mades,columns=['osm_id','man_made','geometry'],crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No buildings or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','man_made','geometry'],crs={'init': 'epsg:4326'})