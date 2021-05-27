"""

  
@Author: Sadhana Nirandjan & Elco Koks  - Institute for Environmental studies, VU University Amsterdam
"""
import numpy as np
import geopandas as gpd
from tqdm import tqdm

#import functions for line_length
from boltons.iterutils import pairwise 
#from geopy.distance import geodesic

#import functions for polygon_area
import pyproj  #and for convert_crs
import shapely.ops as ops
from shapely.geometry.polygon import Polygon
from functools import partial

#import functions for clip_pygeos
import pygeos


########################################################################################################################
################          Fast codes using pygeos          #############################################################
########################################################################################################################
    
def clip_pygeos(df1,df2,spat_tree,reset_index=False):
    """fast clipping using pygeos
    Arguments:
        *df1: dataframe with spatial data to be clipped
        *df2: dataframe with spatial data for mask
        *spat_tree: spatial tree with coordinates in pygeos format
        
    Returns:
        dataframe with coordinates in pygeos geometry
    """
    df1 = df1.loc[spat_tree.query(df2.geometry,predicate='intersects').tolist()]
    df1['geometry'] = pygeos.intersection(df1.geometry,df2.geometry)
    df1 = df1.loc[~pygeos.is_empty(df1.geometry)]
    
    if reset_index==True:
        df1.reset_index(drop=True,inplace=True)

    return df1

def clip_pygeos2(gdf1,gdf2,spat_tree,reset_index=False):
    """fast clipping using pygeos, avoiding errors due to self-intersection (while clipping multipolygons)
    Arguments:
        *gdf1: geodataframe with spatial data to be clipped
        *gdf2: geodataframe with spatial data for mask 
        
    Returns:
        dataframe with coordinates in pygeos geometry
    """
    from shapely.wkb import loads
    geom1 = pygeos.from_shapely(gdf1.geometry.buffer(0)) #.buffer avoids self-intersection error
    geom2 = pygeos.from_shapely(gdf2.geometry)
    geom1 = pygeos.intersection(geom1,geom2)
    gdf1['pygeos_geom'] = geom1
    gdf1 = gdf1.loc[~pygeos.is_empty(gdf1.pygeos_geom)]
    gdf1['geometry'] = gdf1.pygeos_geom.apply(lambda x : loads(pygeos.to_wkb(x))) #transform intersecting geometry back to shapely geometry 
    
    if reset_index==True:
        gdf1.reset_index(drop=True,inplace=True)
    
    return gdf1.drop(columns=['pygeos_geom'])

def convert_crs(geom_series):
    """convert crs to other projection to enable spatial calculations with length and areas
    Arguments:
        *geom_series: series with geographic coordinates in Pygeos format
        
    Returns:
        Serie with coordinates in other projection
    """
    # translate geopandas geometries into pygeos geometries
        
    current_crs="epsg:4326"
    #The commented out crs does not work in all cases
    #current_crs = [*network.edges.crs.values()]
    #current_crs = str(current_crs[0])
    lat = pygeos.geometry.get_y(pygeos.centroid(geom_series[0]))
    lon = pygeos.geometry.get_x(pygeos.centroid(geom_series[0]))
    # formula below based on :https://gis.stackexchange.com/a/190209/80697 
    approximate_crs = "epsg:" + str(int(32700-np.round((45+lat)/90,0)*100+np.round((183+lon)/6,0)))
    #from pygeos/issues/95
    geometries = list(geom_series)
    coords = pygeos.get_coordinates(geometries)
    transformer=pyproj.Transformer.from_crs(current_crs, approximate_crs,always_xy=True)
    new_coords = transformer.transform(coords[:, 0], coords[:, 1])
    
    return pygeos.set_coordinates(geometries.copy(), np.array(new_coords).T)

def line_length_pygeos(geom_series):
    """length per asset in meters
    Arguments:
        *geom_series: series with geographic coordinates in Pygeos format
        
    Returns:
        Serie with length in meters
    """
#    return pygeos.length((geom_series))
    return pygeos.length(convert_crs(geom_series))

def polygon_area_pygeos(geom_series):
    """area per asset in m2
    Arguments:
        *geom_series: series with geographic coordinates in Pygeos format
        
    Returns:
        Serie with area in m2
    """  
    return pygeos.area(convert_crs(geom_series))

def count_per_grid_pygeos(infra_dataset, df_store):
    """count of assets per grid
    Arguments:
        *infra_dataset* : a pd with WGS-84 coordinates in Pygeos 
        *df_store* : pd containing WGS-84 (in Pygeos) coordinates per grid on each row
        
    Returns:
        Count per assets per grid in dataframe with the following format: column => {asset}_count and row => the grid
    """
    asset_list = []

    for asset in infra_dataset.asset.unique():
        if not "{}_count".format(asset) in df_store.columns: df_store.insert(0, "{}_count".format(asset), "") #add assettype as column after first column
        asset_list.append(asset)

    spat_tree = pygeos.STRtree(infra_dataset.geometry) # https://pygeos.readthedocs.io/en/latest/strtree.html
    for grid_cell in tqdm(df_store.itertuples(),total=len(df_store)):
        asset_clip = clip_pygeos(infra_dataset,grid_cell,spat_tree) #clip infra data using GeoPandas clip
        count = asset_clip.asset.value_counts() #count number of assets per asset type

        for asset in asset_list:
            if asset in count.index:
                df_store.loc[grid_cell.Index, "{}_count".format(asset)] = count.get(key = asset)
            else:
                df_store.loc[grid_cell.Index, "{}_count".format(asset)] = 0
    
    return df_store

def length_km_per_grid_pygeos(infra_dataset, df_store):
    """Total length in kilometers per assettype per grid (using Pygeos functions to improve speed)
    Arguments:
        *infra_dataset* : a pd with WGS-84 coordinates in Pygeos 
        *df_store* : pd containing WGS-84 (in Pygeos) coordinates per grid on each row
        
    Returns:
        Length in km per assettype per grid in dataframe with the following format: columns => {asset}_km and rows => the gridcell
    """
    asset_list = []

    for asset in infra_dataset.asset.unique():
        if not "{}_count".format(asset) in df_store.columns: df_store.insert(0, "{}_count".format(asset), "") #add assettype as column after first column for count calculations
        if not "{}_km".format(asset) in df_store.columns: df_store.insert(0, "{}_km".format(asset), "") #add assettype as column after first column for length calculations
        asset_list.append(asset)

    spat_tree = pygeos.STRtree(infra_dataset.geometry) # https://pygeos.readthedocs.io/en/latest/strtree.html
    
    for grid_cell in tqdm(df_store.itertuples(),total=len(df_store)):
        asset_clip = clip_pygeos(infra_dataset,grid_cell,spat_tree) #clip infra data using GeoPandas clip
        
        #count per asset type
        count = asset_clip.asset.value_counts() #count number of assets per asset type
        for asset_type in asset_list:
            if asset_type in count.index:
                df_store.loc[grid_cell.Index, "{}_count".format(asset_type)] = count.get(key = asset_type)
            else:
                df_store.loc[grid_cell.Index, "{}_count".format(asset_type)] = 0

        #calculate length for each asset in clipped infrastructure grid
        asset_clip.insert(1, "length_km", "") #add assettype as column after first column for length calculations
        if not asset_clip.empty:
            geom_series = list(asset_clip.geometry)
            asset_clip["length_km"]=line_length_pygeos(geom_series)/1000 #calculate length per object, transform to km and put in dataframe
        
        length_per_type = asset_clip.groupby(['asset'])['length_km'].sum() #get total length per asset_type in grid

        for asset_type in asset_list:
            if asset_type in length_per_type.index:
                df_store.loc[grid_cell.Index, "{}_km".format(asset_type)] = length_per_type.get(key = asset_type)
            else:
                df_store.loc[grid_cell.Index, "{}_km".format(asset_type)] = 0  
                       
    # print(df_store["{}_km".format(asset_type)])
    # df_store["{}_km".format(asset_type)] = df_store["{}_km".format(asset_type)].astype(float)
    # print(df_store["{}_km".format(asset_type)])
    
    return df_store


def area_km2_per_grid_pygeos(infra_dataset, df_store):
    """Total area in km2 per assettype per grid
    Arguments:
        *infra_dataset* : a pd with WGS-84 coordinates in Pygeos 
        *df_store* : pd containing WGS-84 (in Pygeos) coordinates per grid on each row
        
    Returns:
        Area in km2 per assettype per grid in dataframe with the following format: column => {asset}_km2 and row => the gridcell
    """
    asset_list = []

    for asset in infra_dataset.asset.unique():
        if not "{}_count".format(asset) in df_store.columns: df_store.insert(0, "{}_count".format(asset), "") #add assettype as column after first column for count calculations
        if not "{}_km2".format(asset) in df_store.columns: df_store.insert(0, "{}_km2".format(asset), "") #add assettype as column after first column for area calculations
        asset_list.append(asset)

    spat_tree = pygeos.STRtree(infra_dataset.geometry) # https://pygeos.readthedocs.io/en/latest/strtree.html

    for grid_cell in tqdm(df_store.itertuples(),total=len(df_store)):
        asset_clip = clip_pygeos(infra_dataset, grid_cell,spat_tree) #clip infra data using GeoPandas clip

        #count per asset type
        count = asset_clip.asset.value_counts() #count number of assets per asset type
        for asset_type in asset_list:
            if asset_type in count.index:
                df_store.loc[grid_cell.Index, "{}_count".format(asset_type)] = count.get(key = asset_type)
            else:
                df_store.loc[grid_cell.Index, "{}_count".format(asset_type)] = 0

        #calculate area for each asset in clipped infrastructure grid
        asset_clip.insert(1, "area_km2", "") #add assettype as column after first column for length calculations
        if not asset_clip.empty:
            geom_series = list(asset_clip.geometry)
            asset_clip["area_km2"] = polygon_area_pygeos(geom_series)/1000000 #calculate area per object and put in dataframe

        area_per_type = asset_clip.groupby(['asset'])['area_km2'].sum() #get total length per asset_type in grid
        for asset_type in asset_list:
            if asset_type in area_per_type.index:
                df_store.loc[grid_cell.Index, "{}_km2".format(asset_type)] = area_per_type.get(key = asset_type)
            else:
                df_store.loc[grid_cell.Index, "{}_km2".format(asset_type)] = 0        
        
    return df_store

def get_all_values(nested_dictionary):
    """Get all values in a nested dictionary
    Arguments:
        *nested_dictionary*: dictionary containing keys and values
    """    
    for key, value in nested_dictionary.items():
        if type(value) is dict:
            get_all_values(value)
        else:
            print("{:<28}: {:>30}".format(key, value))

def check_dfs_empty(fetched_data_dict):
    """Check whether dataframes saved in dictionary are all empty

    Argumentss:
        *fetched_data_dict*: dictionary with df saved as valyes

    Returns:
        True if all dataframes are empty, or false when at least one dataframe is not empty 
    """    
    fetched_data_empty = []
    for group in fetched_data_dict:
        fetched_data_empty.append(fetched_data_dict[group].empty)
    
    return all(elem == True for elem in fetched_data_empty)
            
########################################################################################################################
################         Shapely codes          ########################################################################
########################################################################################################################

def count_per_grid(infra_dataset, df_store):
    """ count of assets per grid
    Arguments:
        *infra_dataset* : a shapely Point object with WGS-84 coordinates
        *df_store* : (empty) geopandas dataframe containing coordinates per grid for each grid
        
    Returns:
        Count per assets per grid in dataframe with column = {asset}_count and row = the grid
    """
    asset_list = []

    for asset in infra_dataset.asset.unique():
        if not "{}_count".format(asset) in df_store.columns: df_store.insert(1, "{}_count".format(asset), "") #add assettype as column after first column
        asset_list.append(asset)

    for grid_row in df_store.itertuples():
        grid_cell = grid_row.geometry #select grid
        asset_clip = gpd.clip(infra_dataset, grid_cell) #clip infra data using GeoPandas clip
        count = asset_clip.asset.value_counts() #count number of assets per asset type

        for asset in asset_list:
            if asset in count.index:
                df_store.loc[grid_row.Index, "{}_count".format(asset)] = count.get(key = asset)
            else:
                df_store.loc[grid_row.Index, "{}_count".format(asset)] = 0
    
    return df_store

def line_length(line, ellipsoid='WGS-84'):
    """Length of a line in kilometers, given in geographic coordinates
    Adapted from https://gis.stackexchange.com/questions/4022/looking-for-a-pythonic-way-to-calculate-the-length-of-a-wkt-linestring#answer-115285
    Arguments:
        *line* : a shapely LineString object with WGS-84 coordinates
        
    Optional Arguments:
        *ellipsoid* : string name of an ellipsoid that `geopy` understands (see http://geopy.readthedocs.io/en/latest/#module-geopy.distance)
        
    Returns:
        Length of line in kilometers
    """
    if line.geometryType() == 'MultiLineString':
        return sum(line_length(segment) for segment in line)

    return sum(
        geodesic(tuple(reversed(a)), tuple(reversed(b)), ellipsoid=ellipsoid).kilometers
        for a, b in pairwise(line.coords)
    )

def length_km_per_grid(infra_dataset, df_store):
    """Total length in kilometers per assettype per grid, given in geographic coordinates
    Arguments:
        *infra_dataset* : a shapely Point object with WGS-84 coordinates
        *df_store* : (empty) geopandas dataframe containing coordinates per grid for each grid
        
    Returns:
        Length in km per assettype per grid in dataframe (with column = {asset}_km and row = the grid)
    """
    asset_list = []

    for asset in infra_dataset.asset.unique():
        if not "{}_count".format(asset) in df_store.columns: df_store.insert(1, "{}_count".format(asset), "") #add assettype as column after first column for count calculations
        if not "{}_km".format(asset) in df_store.columns: df_store.insert(1, "{}_km".format(asset), "") #add assettype as column after first column for length calculations
        asset_list.append(asset)

    for grid_row in df_store.itertuples():
        grid_cell = grid_row.geometry #select grid
        try:
            asset_clip = gpd.clip(infra_dataset, grid_cell) #clip infra data using GeoPandas clip

            #count per asset type
            count = asset_clip.asset.value_counts() #count number of assets per asset type
            for asset_type in asset_list:
                if asset_type in count.index:
                    df_store.loc[grid_row.Index, "{}_count".format(asset_type)] = count.get(key = asset_type)
                else:
                    df_store.loc[grid_row.Index, "{}_count".format(asset_type)] = 0

            #calculate length for each asset in clipped infrastructure grid
            asset_clip.insert(1, "length_km", "") #add assettype as column after first column for length calculations
            for line_object in asset_clip['index']:
                asset_clip.loc[line_object, "length_km"] = line_length(asset_clip.loc[asset_clip['index']==line_object].geometry.item()) #calculate length per object and put in dataframe

            length_per_type = asset_clip.groupby(['asset'])['length_km'].sum() #get total length per asset_type in grid
            for asset_type in asset_list:
                if asset_type in length_per_type.index:
                    df_store.loc[grid_row.Index, "{}_km".format(asset_type)] = length_per_type.get(key = asset_type)
                else:
                    df_store.loc[grid_row.Index, "{}_km".format(asset_type)] = 0        

        except: 
            print("Grid number {} raises a ValueError, area has not been clipped".format(grid_row.index))
            for asset_type in asset_list:
                df_store.loc[grid_row.Index, "{}_count".format(asset_type)] = np.nan
                df_store.loc[grid_row.Index, "{}_km".format(asset_type)] = np.nan
        
    return df_store

def polygon_area(polygon_object, ellipsoid='WGS-84'):
    """Area of a polygon in kilometers, given in geographic coordinates
    Adapted from https://gis.stackexchange.com/questions/127607/area-in-km-from-polygon-of-coordinates
    Arguments:
        *polygon_object* : a shapely polygon object with WGS-84 coordinates
    Note: +init syntax is deprecated and will be removed from future versions of PROJ. See https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6
        
    Optional Arguments:
        *ellipsoid* : string name of an ellipsoid that Shapely's `shapely.op.transform` function understands to transform the polygon to projected equal area coordinates and then to take the area.
        
    Returns:
        Area of polygon in squared kilometers
    """
    
    geom_area = ops.transform(
        partial(
            pyproj.transform,
            pyproj.Proj(init='EPSG:4326'),
            pyproj.Proj(
                proj='aea',
                lat_1=polygon_object.bounds[1],
                lat_2=polygon_object.bounds[3])),
        polygon_object)

    return geom_area.area/1000000 #calculate area in m2 and convert to km2 

def area_km2_per_grid(infra_dataset, df_store):
    """Total area in km2 per assettype per grid, given in geographic coordinates
    Arguments:
        *infra_dataset* : a shapely object with WGS-84 coordinates
        *df_store* : (empty) geopandas dataframe containing coordinates per grid for each grid
        
    Returns:
        area in km2 per assettype per grid in dataframe (with column = {asset}_km2 and row = the grid)
    """
    asset_list = []

    for asset in infra_dataset.asset.unique():
        if not "{}_count".format(asset) in df_store.columns: df_store.insert(1, "{}_count".format(asset), "") #add assettype as column after first column for count calculations
        if not "{}_km2".format(asset) in df_store.columns: df_store.insert(1, "{}_km2".format(asset), "") #add assettype as column after first column for area calculations
        asset_list.append(asset)

    for grid_row in df_store.itertuples():
        grid_cell = grid_row.geometry #select grid
        try:
            asset_clip = gpd.clip(infra_dataset, grid_cell) #clip infra data using GeoPandas clip

            #count per asset type
            count = asset_clip.asset.value_counts() #count number of assets per asset type
            for asset_type in asset_list:
                if asset_type in count.index:
                    df_store.loc[grid_row.Index, "{}_count".format(asset_type)] = count.get(key = asset_type)
                else:
                    df_store.loc[grid_row.Index, "{}_count".format(asset_type)] = 0

            #calculate area for each asset in clipped infrastructure grid
            asset_clip.insert(1, "area_km2", "") #add assettype as column after first column for length calculations
            for polygon_object in asset_clip['index']:
                asset_clip.loc[polygon_object, "area_km2"] = polygon_area((asset_clip.loc[asset_clip['index']==polygon_object].geometry.item())) #calculate area per object and put in dataframe

            area_per_type = asset_clip.groupby(['asset'])['area_km2'].sum() #get total length per asset_type in grid
            for asset_type in asset_list:
                if asset_type in area_per_type.index:
                    df_store.loc[grid_row.Index, "{}_km2".format(asset_type)] = area_per_type.get(key = asset_type)
                else:
                    df_store.loc[grid_row.Index, "{}_km2".format(asset_type)] = 0        

        except: 
            print("Grid number {} raises a ValueError, area has not been clipped".format(grid_row.index))
            for asset_type in asset_list:
                df_store.loc[grid_row.Index, "{}_count".format(asset_type)] = np.nan
                df_store.loc[grid_row.Index, "{}_km2".format(asset_type)] = np.nan
    
    return df_store    
