"""
Extract specified keys + values from an OSM pbf-file. This script is based on the fetch.py, but contains improvements. 
Note: pick either the retrieve function using Shapely (if geometry needs to be recognized, e.g. for plotting using Matplotlib), or the retrieve function using pygeos (if geometry does not need to be recognized, e.g. if you want to make a geopackage and export)  

@Author: Sadhana Nirandjan - Institute for Environmental studies, VU University Amsterdam
"""

import geopandas
import pandas
import ogr
import os
import numpy 
import gdal
import pygeos
from tqdm import tqdm
from pygeos import from_wkb
from shapely.wkb import loads

def query_b(geoType,keyCol,**valConstraint):
    """
    This function builds an SQL query from the values passed to the retrieve() function.
    Arguments:
         *geoType* : Type of geometry (osm layer) to search for.
         *keyCol* : A list of keys/columns that should be selected from the layer.
         ***valConstraint* : A dictionary of constraints for the values. e.g. WHERE 'value'>20 or 'value'='constraint'
    Returns:
        *string: : a SQL query string.
    """
    query = "SELECT " + "osm_id"
    for a in keyCol: query+= ","+ a  
    query += " FROM " + geoType + " WHERE "
    # If there are values in the dictionary, add constraint clauses
    if valConstraint: 
        for a in [*valConstraint]:
            # For each value of the key, add the constraint
            for b in valConstraint[a]: query += a + b
        query+= " AND "
    # Always ensures the first key/col provided is not Null.
    query+= ""+str(keyCol[0]) +" IS NOT NULL" 
    return query 


def retrieve_shapely(osm_path,geoType,keyCol,**valConstraint):
    """
    Function to extract specified geometry and keys/values from OpenStreetMap using Shapely
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.     
        *geoType* : Type of Geometry to retrieve. e.g. lines, multipolygons, etc.
        *keyCol* : These keys will be returned as columns in the dataframe.
        ***valConstraint: A dictionary specifiying the value constraints.  
        A key can have multiple values (as a list) for more than one constraint for key/value.  
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all columns, geometries, and constraints specified.    
    """
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)
    query = query_b(geoType,keyCol,**valConstraint)
    sql_lyr = data.ExecuteSQL(query)
    features =[]
    # cl = columns 
    cl = ['osm_id'] 
    for a in keyCol: cl.append(a)
    if data is not None:
        print('query is finished, lets start the loop')
        for feature in tqdm(sql_lyr):
            try:
                if feature.GetField(keyCol[0]) is not None:
                    geom = loads(feature.geometry().ExportToWkb()) 
                    if geom is None:
                        continue
                    # field will become a row in the dataframe.
                    field = []
                    for i in cl: field.append(feature.GetField(i))
                    field.append(geom)   
                    features.append(field)
            except:
                print("WARNING: skipped OSM feature")   
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    
    cl.append('geometry')                   
    if len(features) > 0:
        return geopandas.GeoDataFrame(features,columns=cl,crs={'init': 'epsg:4326'})
    else:
        print("WARNING: No features or No Memory. returning empty GeoDataFrame") 
        return geopandas.GeoDataFrame(columns=['osm_id','geometry'],crs={'init': 'epsg:4326'})
    
def retrieve(osm_path,geoType,keyCol,**valConstraint):
    """
    Function to extract specified geometry and keys/values from OpenStreetMap using pygeos
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.     
        *geoType* : Type of Geometry to retrieve. e.g. lines, multipolygons, etc.
        *keyCol* : These keys will be returned as columns in the dataframe.
        ***valConstraint: A dictionary specifiying the value constraints.  
        A key can have multiple values (as a list) for more than one constraint for key/value.  
    Returns:
        *Panda Core Series* : a frame with all columns, geometries as objects, and constraints specified.    
    """
    driver=ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)
    query = query_b(geoType,keyCol,**valConstraint)
    sql_lyr = data.ExecuteSQL(query)
    features =[]
    # cl = columns 
    cl = ['osm_id'] 
    for a in keyCol: cl.append(a)
    if data is not None:
        print('query is finished, lets start the loop')
        for feature in tqdm(sql_lyr):
            try:
                if feature.GetField(keyCol[0]) is not None:
                    geom = from_wkb(feature.geometry().ExportToWkb()) 
                    if geom is None:
                        continue
                    # field will become a row in the dataframe.
                    field = []
                    for i in cl: field.append(feature.GetField(i))
                    field.append(geom)   
                    features.append(field)
            except:
                print("WARNING: skipped OSM feature")   
    else:
        print("ERROR: Nonetype error when requesting SQL. Check required.")    
    cl.append('geometry')                   
    if len(features) > 0:
        return pandas.DataFrame(features,columns=cl)
    else:
        print("WARNING: No features or No Memory. returning empty GeoDataFrame") 
        return pandas.DataFrame(columns=['osm_id','geometry'])  
    
def merge_energy_datatypes(osm_path):
    """
    Function to extract and merge energy assets with different datatypes from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """  
    #extract line data
    df_line = powerline_limited(osm_path) #extract required data
    if 'asset' in df_line.columns:
        df_line['asset'] = list(map(lambda x: x.lower(), df_line['asset'])) #make sure that asset column is in lowercase characters
        #reclassify assets 
        mapping_dict = {
            "cable" : "cable", #underground
            "minor_cable" : "cable", 
            #"generator" : "generator", #device used to convert power from one form to another
            "line" : "line", #overground
            "minor_line" : "minor_line", #overground
            #"plant" : "plant", #place where power is generated
            #"substation" : "substation"
        }
        df_line['asset'] = df_line.asset.apply(lambda x : mapping_dict[x])  #reclassification 

    if 'voltage' in df_line.columns:
        df_line = df_line.drop(['voltage'], axis=1) 
    
    #extract polygon data
    df_poly = power_polygon(osm_path) #extract required data
    df_poly['geometry'] =pygeos.buffer(df_poly.geometry,0) #avoid intersection
    
    #extract point data
    df_point = power_point(osm_path) #extract required data
    
    return pandas.concat([df_line, df_poly, df_point], ignore_index=True)

def powerline_limited(osm_path):
    """
    Function to extract energy linestrings from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    return (retrieve(osm_path,'lines',['power','voltage'],**{'power':["='cable' or ","='line' or ","='minor_line' or ","='minor_cable'"]})).rename(columns={'power': 'asset'}) 

def powerline(osm_path):
    """
    Function to extract energy linestrings from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    return (retrieve(osm_path,'lines',['power','voltage'],**{'power':["='cable' or ","='line' or ","='minor_line' or ","='minor_cable' or ","='plant' or ","='substation'"]})).rename(columns={'power': 'asset'}) 
    
def powerline_all(osm_path):
    """
    Function to extract all energy linestrings from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    return retrieve(osm_path,'lines',['power', 'voltage']) 

def power_polygon(osm_path):
    """
    Function to extract energy polygons from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    df = retrieve(osm_path,'multipolygons',['other_tags']) 
    
    df = df.loc[(df.other_tags.str.contains('power'))]   #keep rows containing power data         
    df = df.reset_index(drop=True).rename(columns={'other_tags': 'asset'})     
    
    df['asset'].loc[df['asset'].str.contains('"power"=>"substation"', case=False)]  = 'substation' #specify row
    df['asset'].loc[df['asset'].str.contains('"power"=>"plant"', case=False)] = 'plant' #specify row
    
    df = df.loc[(df.asset == 'substation') | (df.asset == 'plant')]
            
    return df.reset_index(drop=True) 

def power_point(osm_path):
    """
    Function to extract energy points from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    df = retrieve(osm_path,'points',['other_tags']) 
    
    df = df.loc[(df.other_tags.str.contains('power'))]  #keep rows containing power data       
    df = df.reset_index(drop=True).rename(columns={'other_tags': 'asset'})     
    
    df['asset'].loc[df['asset'].str.contains('"power"=>"tower"', case=False)]  = 'power_tower' #specify row
    df['asset'].loc[df['asset'].str.contains('"power"=>"pole"', case=False)] = 'power_pole' #specify row
    
    df = df.loc[(df.asset == 'power_tower') | (df.asset == 'power_pole')]
            
    return df.reset_index(drop=True)   

def power_polygon_old(osm_path):
    """
    Function to extract energy polygons from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    df = retrieve(osm_path,'multipolygons',['other_tags']) 

    for row in df.itertuples():
        if df.loc[row.Index, "other_tags"] == None:
            df = df.drop(row.Index)
        elif not 'power' in df.loc[row.Index, "other_tags"]:
            df = df.drop(row.Index)
            
    df = df.reset_index(drop=True).rename(columns={'other_tags': 'asset'})     
            
    for row in range(len(df.index)):
        if '"power"=>"substation"' in df["asset"][row]:
            df["asset"][row] = 'substation' 
        elif '"power"=>"plant"' in df["asset"][row]:
            df["asset"][row] = 'plant'
        else:
            df = df.drop(index=row)
            
    return df.reset_index(drop=True) 
           
def power_point_old(osm_path):
    """
    Function to extract energy points from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    df = retrieve(osm_path,'points',['other_tags']) 

    for row in df.itertuples():
        if df.loc[row.Index, "other_tags"] == None:
            df = df.drop(row.Index)
        elif not 'power' in df.loc[row.Index, "other_tags"]:
            df = df.drop(row.Index)
            
    df = df.reset_index(drop=True).rename(columns={'other_tags': 'asset'})     
    
    for row in range(len(df.index)):
        if '"power"=>"tower"' in df["asset"][row]:
            df["asset"][row] = 'power_tower' 
        elif '"power"=>"pole"' in df["asset"][row]:
            df["asset"][row] = 'power_pole'
        else:
            df = df.drop(index=row)
            
    return df.reset_index(drop=True)  

def electricity(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.   
    """    
    return retrieve(osm_path,'lines',['power','voltage'],**{'voltage':[" IS NULL"],})

def roads_all(osm_path):
    """
    Function to extract road linestrings from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique road linestrings.
    """   
    return (retrieve(osm_path,'lines',['highway'])).rename(columns={'highway': 'asset'}) 

def roads(osm_path):
    """
    Function to extract road linestrings categorized as primary, secondary and tertiary roads from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique road linestrings.
    """   
    return (retrieve(osm_path,'lines',['highway'],**{'highway':["='motorway' or ","='motorway_link' or ","='trunk' or ","='trunk_link' or ","='primary' or ","='primary_link' or ","='secondary' or ","='secondary_link' or ","='tertiary' or ","='tertiary_link' or ","='residential' or ","='road' or ","='unclassified' or ","='living_street'"]})).rename(columns={'highway': 'asset'})  
    
def mainRoads(osm_path):
    """
    Function to extract main road linestrings from OpenStreetMap    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique main road linestrings.   
    """ 
    return retrieve(osm_path,'lines',['highway','oneway','lanes','maxspeed'],**{'highway':["='primary' or ","='trunk' or ","='motorway' or ","='motorway_link' or ","='trunk_link' or ","='primary_link' or ", "='secondary' or ","='tertiary' or ","='tertiary_link'"]})
                                                               
def airports(osm_path):
    """
    Function to extract airport multipolygons from OpenStreetMap    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique airport multipolygons.   
    """ 
    return (retrieve(osm_path,'multipolygons',['aeroway'],**{'aeroway':["='aerodrome'"]})).rename(columns={'aeroway': 'asset'}) 

def railway_service(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique land-use polygons.
    """ 
    return retrieve(osm_path,'lines',['railway','service'],**{"service":[" IS NOT NULL"]})

def railway_all(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique railway linesstrings.
    """ 
    return (retrieve(osm_path,'lines',['railway'])).rename(columns={'railway': 'asset'}) 


def railway(osm_path):
    """
    Function to extract railway linestrings from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique railway linesstrings.
    """ 
    return (retrieve(osm_path,'lines',['railway'],**{'railway':["='rail' or ","='tram' or ","='subway' or ","='construction' or ","='funicular' or ","='light_rail' or ","='narrow_gauge'"]})).rename(columns={'railway': 'asset'}) 

def railway_stops(osm_path):
    """
    Function to extract railway nodes from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique railway nodes.
    """ 
    return retrieve(osm_path,'points',['railway'],**{'railway':["='halt' or ","='subway_entrance' or ","='tram_stop'"]})

def railway_areas(osm_path):
    """
    Function to extract railway polygons from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique railway multipolygons.
    """ 
    return retrieve(osm_path,'multipolygons',['railway','landuse'],**{'railway':["='platform' or ","='station' or ","='tram_stop'"],'landuse':["='railway'"]})

def ports(osm_path):
    """
    Function to extract port polygons from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique port multipolygons.
    """ 
    return (retrieve(osm_path,'multipolygons',['landuse'],**{'landuse':["='industrial' or ","='port' or ","='harbour'"]})).rename(columns={'landuse': 'asset'}) 

def ferries(osm_path):
    """
    Function to extract road linestrings from OpenStreetMap
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique road linestrings.
    """
    return retrieve(osm_path,'lines',['route'],**{"route":["='ferry'",]})

def water_supply(osm_path):
    """
    Function to extract water_supply polygons from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique water_supply multipolygons.
    """ 
    i = retrieve(osm_path,'multipolygons',['man_made'],**{'man_made':["='water_tower' or ","='water_well' or ","='reservoir_covered' or ","='water_works'"]})
    j = retrieve(osm_path,'multipolygons',['landuse'],**{'landuse':["='reservoir'"]})
    
    i = i.rename(columns={'man_made': 'asset'})
    j = j.rename(columns={'landuse': 'asset'})
    
    combined_df = pandas.concat([i,j], ignore_index=True, sort=False) #append objects while ignoring that they may have overlapping index
    if combined_df.empty == True:
        return combined_df
    else:
        return combined_df[["osm_id","asset","geometry"]] 

def waste_solid(osm_path):
    """
    Function to extract solid waste polygons from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique solid waste multipolygons.
    """ 
    i = retrieve(osm_path,'multipolygons',['amenity'],**{'amenity':["='waste_transfer_station'"]})
    j = retrieve(osm_path,'multipolygons',['landuse'],**{'landuse':["='landfill'"]})
    
    i = i.rename(columns={'amenity': 'asset'})
    j = j.rename(columns={'landuse': 'asset'})
    
    combined_df = pandas.concat([i,j], ignore_index=True, sort=False) #append objects while ignoring that they may have overlapping index
    if combined_df.empty == True:
        return combined_df
    else:
        return combined_df[["osm_id","asset","geometry"]] 

def waste_water(osm_path):
    """
    Function to extract water waste polygons from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique water waste multipolygons.
    """ 
    return (retrieve(osm_path,'multipolygons',['man_made'],**{'man_made':["='wastewater_plant'"]})).rename(columns={'man_made': 'asset'}) 

def telecom(osm_path):
    """
    Function to combine extracted telecommunication tower nodes from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique telecom nodes.
    """ 
    i = telecom_towers(osm_path)
    j = telecom_mast(osm_path)
    
    combined_df = pandas.concat([i,j], ignore_index=True, sort=False) #append objects while ignoring that they may have overlapping index
    if combined_df.empty == True:
        return combined_df
    else:
        return combined_df[["osm_id","asset","geometry"]] 

def telecom_mast(osm_path):
    """
    Function to extract telecommunication masts nodes from OpenStreetMap. See detailted information telecommunication masts: https://wiki.openstreetmap.org/wiki/Tag%3Aman_made%3Dmastr   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique telecommunication tower nodes.
    """ 
    df = retrieve(osm_path,'points',['man_made','other_tags'],**{"man_made":["='mast'"]}).rename(columns={'man_made': 'asset'}) 
    
    #only towers that are specifically functioning as telecommunication tower will be saved 
    for row in df.itertuples():
        if df.loc[row.Index, "other_tags"] == None:
            df = df.drop(row.Index)
        elif not 'tower:type"=>"communication' in df.loc[row.Index, "other_tags"]:
            df = df.drop(row.Index)
            
    return df.reset_index(drop=True) 

def telecom_towers(osm_path):
    """
    Function to combine extracted telecommunication tower nodes from OpenStreetMap   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique telecom nodes.
    """ 
    b = telecom_towers_big(osm_path)
    s = telecom_towers_small(osm_path)
    
    combined_df = pandas.concat([s,b], ignore_index=True, sort=False) #append objects while ignoring that they may have overlapping index
    if combined_df.empty == True:
        return combined_df
    else:
        return combined_df[["osm_id","asset","geometry"]] 

def telecom_towers_big(osm_path):
    """
    Function to extract big communication tower nodes from OpenStreetMap. See detailed information big communication towers: https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dcommunications_tower   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique big communication tower nodes.
    """   
    
    return (retrieve(osm_path,'points',['man_made'],**{'man_made':["='communications_tower'"]})).rename(columns={'man_made': 'asset'}) 

def telecom_towers_small(osm_path):
    """
    Function to extract small telecommunication tower nodes from OpenStreetMap. See detailted information telecommunication towers: https://wiki.openstreetmap.org/wiki/Tag%3Aman_made%3Dtower   
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique telecommunication tower nodes.
    """ 
    df = retrieve(osm_path,'points',['man_made','other_tags'],**{"man_made":["='tower'"]}).rename(columns={'man_made': 'asset'}) 
    
    #only towers that are specifically functioning as telecommunication tower will be saved 
    for row in df.itertuples():
        if df.loc[row.Index, "other_tags"] == None:
            df = df.drop(row.Index)
        elif not 'tower:type"=>"communication' in df.loc[row.Index, "other_tags"]:
            df = df.drop(row.Index)
            
    return df.reset_index(drop=True) 

def telecom_towers_small2(osm_path):
    """
    Function to extract small telecom nodes from OpenStreetMap. Please note that when using this function, 
    that towers that are missing additional information stored under 'other tags' are included as well in final output    
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique telecom nodes.
    """ 
    df = retrieve(osm_path,'points',['man_made','other_tags'],**{"man_made":["='tower'"]})
    
    telecom_towers = geopandas.GeoDataFrame(columns=['osm_id','man_made','other_tags','geometry'])

    for row in range(len(df.index)):
        if df["other_tags"][row] != None:
            if 'tower:type"=>"communication' in df["other_tags"][row]:
                telecom_towers = telecom_towers.append(df.loc[row])
            
    return telecom_towers.reset_index(drop=True)

def telecom_towers_small1(osm_path):
    """
    Function to extract small telecommunication tower nodes from OpenStreetMap. Please note that when using this function, 
    that towers that are missing additional information stored under 'other tags' are included as well in final output 
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with all unique telecom nodes.
    """ 
    df = retrieve(osm_path,'points',['man_made','other_tags'],**{"man_made":["='tower'"]}).rename(columns={'man_made': 'asset'}) 

    for row in reversed(range(len(df.index))):
        if df["other_tags"][row] != None:
            if not 'tower:type"=>"communication' in df["other_tags"][row]:
                df = df.drop(df.index[row])
                
    return df.reset_index(drop=True)

def social_amenity(osm_path):
    """
    Function to extract healthcare polygons from OpenStreetMap that are categorized under the key 'amenity'  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare polygons.
    """   
    return (retrieve(osm_path,'multipolygons',['amenity'],**{'amenity':["='hospital' or ","='doctors' or ","='clinic' or ","='dentist' or ","='pharmacy'"]})).rename(columns={'amenity': 'asset'}) 

def healthcare_filter(df_all):
    """
    Function for consistently formatting of extracted healthcare data    
    Arguments:
        *df_all* : DataFrame with extracted assets that are categorized under key 'healthcare'        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare polygons with correct format.
    """   
    #get requested assets under healthcare tag           
    df_filtered = pandas.DataFrame(columns=['osm_id','asset','geometry']) #create df for saving data
    for row in range(len(df_all.index)): 
        if 'healthcare' in df_all["asset"][row]: #check if healthcare key is present
            df_filtered = df_filtered.append(df_all.loc[row]) #if so, save in df       
            if '"healthcare"=>"doctor"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'doctors' #to be consistent with asset list 
            elif '"healthcare"=>"pharmacy"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'pharmacy'
            elif '"healthcare"=>"hospital"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'hospital'
            elif '"healthcare"=>"clinic"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'clinic'
            elif '"healthcare"=>"dentist"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'dentist'
            elif '"healthcare"=>"physiotherapist"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'physiotherapist'
            elif '"healthcare"=>"alternative"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'alternative'
            elif '"healthcare"=>"laboratory"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'laboratory'
            elif '"healthcare"=>"optometrist"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'optometrist'
            elif '"healthcare"=>"rehabilitation"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'rehabilitation'
            elif '"healthcare"=>"blood_donation"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'blood_donation'
            elif '"healthcare"=>"birthing_center"' in df_filtered["asset"][row]:
                df_filtered["asset"][row] = 'birthing_center'
            else:
                df_filtered = df_filtered.drop(index=row)
                
    return df_filtered

def social_healthcare(osm_path):
    """
    Function to extract healthcare polygons from OpenStreetMap that are categorized under the key 'healthcare'  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare polygons.
    """   
    df_all = retrieve(osm_path,'multipolygons',['other_tags', 'amenity']).rename(columns={'other_tags': 'asset'}) 
    
    #delete rows that are duplicates of social_amenity
    asset_list = ['hospital', 'doctors', 'clinic', 'dentist', 'pharmacy'] #note that this list of assets should be similar to assets extracted in def social_amenity
    for asset in asset_list:
        index_delete = df_all[(df_all['amenity'] == asset)].index
        df_all.drop(index_delete,inplace=True)
    df_all = df_all.drop(['amenity'], axis=1).reset_index(drop=True) #drop amenity column, reset index
    
    #get requested assets           
    df = healthcare_filter(df_all)
             
    return df.reset_index(drop=True)

def social_infrastructure_polygon(osm_path):
    """
    Function to append unique health infrastructure assets extracted from keys 'amenity' and 'healthcare'  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare polygons.
    """   
    df1 = social_amenity(osm_path)
    df2 = social_healthcare(osm_path)
    
    return (df1.append(df2)).reset_index(drop=True)

def social_infrastructure_point(osm_path):
    """
    Function to extract healthcare point data from OpenStreetMap categorized under keys 'healthcare' and 'amenity'  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare point data.
    """   
    df_all = retrieve(osm_path,'points',['other_tags']).rename(columns={'other_tags': 'asset'}) 
    
    #get requested healthcare assets categorized under the key 'healthcare' with correct formatting          
    df_h = healthcare_filter(df_all)
                
    #get requested healthcare assets categorized under the key 'amenity'           
    df_a = pandas.DataFrame(columns=['osm_id','asset','geometry']) #create df for saving data
    for row in range(len(df_all.index)): 
        if 'amenity' in df_all["asset"][row]: 
            if not 'healthcare' in df_all["asset"][row]: #check if healthcare key is present
                df_a = df_a.append(df_all.loc[row]) #if so, save in df
                
                if '"amenity"=>"doctors"' in df_a["asset"][row]:
                    df_a["asset"][row] = 'doctors' #to be consistent with asset list 
                elif '"amenity"=>"pharmacy"' in df_a["asset"][row]:
                    df_a["asset"][row] = 'pharmacy'
                elif '"amenity"=>"hospital"' in df_a["asset"][row]:
                    df_a["asset"][row] = 'hospital'
                elif '"amenity"=>"clinic"' in df_a["asset"][row]:
                    df_a["asset"][row] = 'clinic'
                elif '"amenity"=>"dentist"' in df_a["asset"][row]:
                    df_a["asset"][row] = 'dentist'
                else:
                    df_a = df_a.drop(index=row)
                
    df_social_points = df_a.append(df_h)
                
    return df_social_points.reset_index(drop=True)

def compare_polygon_to_point(df_point, df_polygon):
    """
    Function that removes polygons with overlapping points if asset type is similar    
    Arguments:
        *df_point* : a geopandas GeoDataFrame with specified unique healthcare point data.
        *df_polygon* : a geopandas GeoDataFrame with specified unique healthcare polygons.       
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare assets
    """   

    #check for each polygon which points are overlaying with it 
    df_polygon['geometry'] = pygeos.buffer(df_polygon.geometry,0) #avoid intersection
    spat_tree = pygeos.STRtree(df_point.geometry) # https://pygeos.readthedocs.io/en/latest/strtree.html
    for polygon_row in df_polygon.itertuples():
        df_point_overlap = (df_point.loc[spat_tree.query(polygon_row.geometry,predicate='intersects').tolist()]).sort_index(ascending=True) #get point that overlaps with polygon
        if not df_point_overlap.empty:
            if polygon_row.asset in df_point_overlap['asset'].tolist():
                df_polygon = df_polygon.drop(polygon_row.Index)
    
    return df_polygon.reset_index(drop=True)

def social_infrastructure_combined(osm_path):
    """
    Function that extracts, filters and combines point and polygon healthcare OpenStreetMap data categorized under the keys 'healthcare' and 'amenity'  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique healthcare point data.
    """   
    df_point = social_infrastructure_point(osm_path)
    df_polygon = social_infrastructure_polygon(osm_path)
    
    df_polygon_filtered = compare_polygon_to_point(df_point, df_polygon) #remove duplicates polygon and point data 
    df_polygon_filtered['geometry'] = pygeos.centroid(df_polygon_filtered.geometry) #transform to pointdata
    
    return (df_point.append(df_polygon_filtered)).reset_index(drop=True)

def education(osm_path):
    """
    Function to extract energy linestrings from OpenStreetMap  
    Arguments:
        *osm_path* : file path to the .osm.pbf file of the region 
        for which we want to do the analysis.        
    Returns:
        *GeoDataFrame* : a geopandas GeoDataFrame with specified unique energy linestrings.
    """   
    return (retrieve(osm_path,'multipolygons',['amenity'],**{'amenity':["='college' or ","='kindergarten' or ","='library' or ","='school' or ","='university'"]})).rename(columns={'amenity': 'asset'}) 
