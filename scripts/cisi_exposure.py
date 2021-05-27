"""

  
@Authors: Sadhana Nirandjan & Elco Koks - Institute for Environmental studies, VU University Amsterdam
"""
import os,sys
import pandas as pd
import numpy as np
import geopandas as gpd
import rasterio
#!pip install geopy
#!pip install boltons
from pathlib import Path
from tqdm import tqdm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from rasterio.plot import show
from IPython.display import display #when printing geodataframes, put it in columns -> use display(df)
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator, LinearLocator, MaxNLocator)
import pygeos
#from pgpkg import Geopackage
import matplotlib.pyplot as plt
import copy

#sys.path.append("C:\Projects\Coastal_Infrastructure\scripts")
import fetch
import cisi
plt.rcParams['figure.figsize'] = [20, 20]

#from osgeo import gdal
#gdal.SetConfigOption("OSM_CONFIG_FILE", os.path.join("..","osmconf.ini"))
    
########################################################################################################################
################          Functions for exposure index calculations                #####################################
########################################################################################################################
        
def base_calculations(infrastructure_systems, fetched_data_dict, grid_data):
    """ count/length/area of assets per grid in a dictionary containing df's for each subsystem
    Arguments:
        *continent* : continent in which area is situated
        *area* : area to be analyzed
        *degree* : the gridsize at which calculations will take place
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        
    Returns:
        dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
    """
    #use keys in infrastructure_systems to make dataframes for indices https://stackoverflow.com/questions/56217737/use-elements-in-a-list-for-dataframe-names
    cisi_exposure = {ci_system: grid_data.copy() for ci_system in infrastructure_systems}                 
    print("The counts, lengths and areas of each asset will now be calculated for each grid cell")

    #loop through infrastructure systems
    for ci_system in infrastructure_systems:
        print("The loop starts for subsystem {} with assets for the following groups {}".format(ci_system, infrastructure_systems[ci_system]))
        for value in infrastructure_systems[ci_system]:
            if fetched_data_dict[value].empty == False:  
                #check single datatype or multiple in one df? 
                list_datatypes = unique_datatypes(fetched_data_dict[value])
                if len(list_datatypes) == 1:               
                    # perform base calculations for one datatype
                    geometry_type = pygeos.geometry.get_type_id(fetched_data_dict[value].iloc[0]["geometry"]) #get geometry id
                    if geometry_type == 0: #point
                        #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                        cisi_exposure[ci_system] = cisi.count_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system]) 
                    elif  geometry_type == 1: #"linestring" in geometry_type:
                        #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                        cisi_exposure[ci_system] = cisi.length_km_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])
                    elif  geometry_type == 3: #"polygon" in geometry_type:
                        #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                        fetched_data_dict[value]['geometry'] =pygeos.buffer(fetched_data_dict[value].geometry,0)
                        cisi_exposure[ci_system] = cisi.area_km2_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])
                    elif  geometry_type == 5: #"multilinestring" in geometry_type:
                        #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                        cisi_exposure[ci_system] = cisi.length_km_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])
                    elif  geometry_type == 6: #"multipolygon" in geometry_type:
                        #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                        fetched_data_dict[value]['geometry'] = pygeos.buffer(fetched_data_dict[value].geometry,0)
                        cisi_exposure[ci_system] = cisi.area_km2_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])                        
                    else: 
                        print("WARNING: fetched data '{}' contains an unexpected geometry type {}".format(value, geometry_type))
                elif len(list_datatypes) > 1:
                        cisi_exposure[ci_system] = base_calculations_multipledatatypes(list_datatypes, fetched_data_dict[value], cisi_exposure[ci_system])
                else:
                    print("WARNING: geodataframe contains no data: {}.".format(value))
            else:
                print("WARNING: the following group does not exist: {}. Empty df is returned".format(value))

        #convert objects to float (to avoid problems with plotting later on)
        for col in cisi_exposure[ci_system].columns:
            if "_count" in col or "_km" in col or "_km2" in col:
                cisi_exposure[ci_system][col] = cisi_exposure[ci_system][col].astype(float)
            #else:
            #    print("The following column is not converted into a float: {} ".format(col))

    #temporary lines to get the max values 
    #print("Overview of maxima:")
    #for ci_system in cisi_exposure:
    #    for col in cisi_exposure[ci_system].columns:
    #        if 'index' not in col and 'Index' not in col and 'geometry' not in col:
    #            print("Maximum of {:<25}: {:>30}".format(col, cisi_exposure[ci_system][col].max()))

    return cisi_exposure

def base_calculations_multipledatatypes(list_datatypes, infra_dataset, df_store):
    """base calculations for df with multiple datatypes (e.g. point, line, polygon)
    Arguments:
        *infra_dataset* : a pd with WGS-84 coordinates in Pygeos 
        *df_store* : pd containing WGS-84 (in Pygeos) coordinates per grid on each r 
        
    Returns:
        df of a subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
    """
    import copy 
    df_final = copy.deepcopy(df_store)
     
    #multiple datatypes in one df
    infra_dataset['datatype'] = pygeos.geometry.get_type_id(infra_dataset["geometry"]) #add column specifying datatype
    infra_dataset["datatype"].replace({1:5, 3:6}, inplace=True) #do not differentiate between linestrings-multilinestrings, polygons-multipolygons
    
    for item in list_datatypes:
        if item == 0: #point data
            df_store_point = copy.deepcopy(df_store)
            point_df = infra_dataset[infra_dataset['datatype'] == 0].drop(['datatype'], axis=1).reset_index(drop=True)
            grid_point_df = cisi.count_per_grid_pygeos(point_df, df_store_point)
            df_final = pd.concat([df_final, grid_point_df.drop(['geometry', 'grid_number'], axis=1)], axis=1)
        elif item == 5: #line data
            df_store_line = copy.deepcopy(df_store) 
            line_df = infra_dataset[infra_dataset['datatype'] == 5].drop(['datatype'], axis=1).reset_index(drop=True)
            grid_line_df = cisi.length_km_per_grid_pygeos(line_df, df_store_line)
            df_final = pd.concat([df_final, grid_line_df.drop(['geometry', 'grid_number'], axis=1)], axis=1)
        elif item == 6: #polygon data
            df_store_polygon = copy.deepcopy(df_store)
            polygon_df = infra_dataset[infra_dataset['datatype'] == 6].drop(['datatype'], axis=1).reset_index(drop=True)
            grid_polygon_df = cisi.area_km2_per_grid_pygeos(polygon_df, df_store_polygon)
            df_final = pd.concat([df_final, grid_polygon_df.drop(['geometry', 'grid_number'], axis=1)], axis=1)
    
    #put geometry as last column
    geo_col = df_final['geometry']
    df_final = df_final.drop(['geometry'],axis=1)
    df_final['geometry'] = geo_col

    return df_final

def base_calculations_original(infrastructure_systems, fetched_data_dict, grid_data):
    """ count/length/area of assets per grid in a dictionary containing df's for each subsystem
    Arguments:
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *fetched_data_dict* : dictionairy containing the subsystems as keys and dataframes with spatial data as values 
        *grid_data* : dataframe with spatial grids
        
    Returns:
        dictionary consisting of a df for each subsystem holding the count, length, or area per asset per grid (EPSG:4326 in Pygeos geometry)
    """
    #use keys in infrastructure_systems to make dataframes for indices https://stackoverflow.com/questions/56217737/use-elements-in-a-list-for-dataframe-names
    cisi_exposure = {ci_system: grid_data.copy() for ci_system in infrastructure_systems}                 
    print("The counts, lengths and areas of each asset will now be calculated for each grid cell")

    #loop through infrastructure systems
    for ci_system in infrastructure_systems:
        print("The loop starts for subsystem {} with assets for the following groups {}".format(ci_system, infrastructure_systems[ci_system]))
        for value in infrastructure_systems[ci_system]:
            if fetched_data_dict[value].empty == False:
                # perform base calculations
                geometry_type = pygeos.geometry.get_type_id(fetched_data_dict[value].iloc[0]["geometry"]) #get geometry id
                if geometry_type == 0: #point
                    #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                    cisi.count_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system]) 
                elif  geometry_type == 1: #"linestring" in geometry_type:
                    #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                    cisi.length_km_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])
                elif  geometry_type == 3: #"polygon" in geometry_type:
                    #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                    fetched_data_dict[value]['geometry'] =pygeos.buffer(fetched_data_dict[value].geometry,0)
                    cisi.area_km2_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])
                elif  geometry_type == 5: #"multilinestring" in geometry_type:
                    #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                    cisi.length_km_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system]) 
                elif  geometry_type == 6: #"multipolygon" in geometry_type:
                    #print("{}_{}.gpkg".format(area, value), "has geometrytype", geometry_file)
                    fetched_data_dict[value]['geometry'] = pygeos.buffer(fetched_data_dict[value].geometry,0)
                    cisi.area_km2_per_grid_pygeos(fetched_data_dict[value], cisi_exposure[ci_system])                        
                else: 
                    print("WARNING: fetched data '{}' contains an unexpected geometry type {}".format(value, geometry_type))
            else:
                print("WARNING: the following group does not exist: {}. Empty df is returned".format(value))

        #convert objects to float (to avoid problems with plotting later on)
        for col in cisi_exposure[ci_system].columns:
            if "_count" in col or "_km" in col or "_km2" in col:
                cisi_exposure[ci_system][col] = cisi_exposure[ci_system][col].astype(float)
            #else:
            #    print("The following column is not converted into a float: {} ".format(col))

    #temporary lines to get the max values 
    #print("Overview of maxima:")
    #for ci_system in cisi_exposure:
    #    for col in cisi_exposure[ci_system].columns:
    #        if 'index' not in col and 'Index' not in col and 'geometry' not in col:
    #            print("Maximum of {:<25}: {:>30}".format(col, cisi_exposure[ci_system][col].max()))

    return cisi_exposure

def unique_datatypes(gdf):
    """Check whether gdf contains multiple datatypes
    Arguments:
        *gdf1: geodataframe with spatial data
        
    Returns:
        list with unique datatypes in pygeos language
    """
    check_datatypes = pygeos.geometry.get_type_id(gdf["geometry"])
    list_datatypes = list(check_datatypes.unique())
    for index, item in enumerate(list_datatypes):
        if item == 1: #model does not differentiate between strings and multistrings
            list_datatypes[index] = 5
        elif item == 3: #model does not differentiate between polygon and multipolygons
            list_datatypes[index] = 6
    list_datatypes = list(set(list_datatypes)) #unique datatypes in list
    
    return list_datatypes

    ########################################################################################################################
########     Functions for exposure index calculations when areas to be analyzed are saved in one single grid-file  ############
    ########################################################################################################################

def cisi_overall_max_single(weight_assets, weight_groups, weight_subsystems,infrastructure_systems, cisi_exposure_base):
    """function to calculate the indices 
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)   
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on the max of the area as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using max")
    
    cisi_exposure = copy.deepcopy(cisi_exposure_base) #to avoid problems later on when cisi_exposure is returned
    #firstly, make indices based on assets to make the conversion to an index per groups/values       
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system]["Index_{}".format(value)] = 0 #create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]: 
                if asset in cisi_exposure[ci_system].columns: #check whether asset in dictioniary exists in cisi exposure geodataframe
                    #conversion 1
                    if cisi_exposure[ci_system][asset].max() != 0:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/cisi_exposure[ci_system][asset].max() #add column km/max km, calculate asset index
                    else:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = 0.0 
                    #conversion 2
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)]*(weight_assets[ci_system][value][asset]) #assetgroup index     
                else:
                    print("\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure dataframes: {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(asset))

            #normalization conversion 2
            if cisi_exposure[ci_system]["Index_{}".format(value)].max() != 0:
                cisi_exposure[ci_system]["Index_{}".format(value)] = cisi_exposure[ci_system]["Index_{}".format(value)]/cisi_exposure[ci_system]["Index_{}".format(value)].max()
            else:
                cisi_exposure[ci_system]["Index_{}".format(value)] = 0.0 

        #make indices based on value/groups to make the conversion to an index per system 
        #conversion 3
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]: 
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)]*(weight_groups[ci_system][value]) #calculate subsystem index

        #normalization conversion 3
        if cisi_exposure[ci_system]["Index_{}".format(ci_system)].max() != 0:
            cisi_exposure[ci_system]["Index_{}".format(ci_system)] = cisi_exposure[ci_system]["Index_{}".format(ci_system)]/cisi_exposure[ci_system]["Index_{}".format(ci_system)].max()

    #lastly, make final exposure index based on the subsystem 
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)

    return exposure_index,cisi_exposure

def cisi_overall_max_single_no_normalization(weight_assets, weight_groups, weight_subsystems,infrastructure_systems, cisi_exposure_base):
    """function to calculate the indices 
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)   
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on the max of the area as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using max")
    
    cisi_exposure = copy.deepcopy(cisi_exposure_base) #to avoid problems later on when cisi_exposure is returned
    #firstly, make indices based on assets to make the conversion to an index per groups/values       
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system]["Index_{}".format(value)] = 0 #create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]: 
                if asset in cisi_exposure[ci_system].columns: #check whether asset in dictioniary exists in cisi exposure geodataframe
                    if cisi_exposure[ci_system][asset].max() != 0:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/cisi_exposure[ci_system][asset].max() #add column km/max km, calculate asset index
                    else:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = 0.0 
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)]*(weight_assets[ci_system][value][asset]) #assetgroup index     
                else:
                    print("\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure dataframes: {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(asset))

        #secondly, make indices based on value/groups to make the conversion to an index per subsystem 
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]: 
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)]*(weight_groups[ci_system][value]) #calculate subsystem index

    #lastly, make final exposure index based on the subsystem 
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)
            
    return exposure_index,cisi_exposure

def cisi_overall_mean_single(weight_assets, weight_groups, weight_subsystems, infrastructure_systems,cisi_exposure_base):
    """function to calculate the indices 
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value.
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on the mean of the area as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using mean")
  
    cisi_exposure = copy.deepcopy(cisi_exposure_base) #to avoid problems later on when cisi_exposure is returned
    #firstly, make indices based on assets to make the conversion to an index per groups/values       
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system]["Index_{}".format(value)] = 0 #create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]: 
                if asset in cisi_exposure[ci_system].columns: #check whether asset in dictioniary exists in cisi exposure geodataframe 
                    #get the mean ignoring zeros
                    temp = copy.deepcopy(cisi_exposure[ci_system][asset])
                    temp[temp == 0] = np.nan
                    if temp.isnull().all() == False: #whole column does not contain nans
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/temp.mean() #add column km/max km, calculate asset index
                    else:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = 0.0
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)]*(weight_assets[ci_system][value][asset]) #assetgroup index           
                else:
                    print("\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure dataframes: {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(asset))

        #secondly, make indices based on value/groups to make the conversion to an index per subsystem 
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]: 
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)]*(weight_groups[ci_system][value]) #calculate subsystem index

    #lastly, make final exposure index based on the subsystem 
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)
            
    return exposure_index,cisi_exposure
    
    
    ########################################################################################################################
########     Functions for exposure index calculations when areas to be analyzed are saved in multiple grid-files  ############
    ########################################################################################################################
    
def cisi_max_per_area(weight_assets, weight_groups, weight_subsystems, continent,area,degree,infrastructure_systems, cisi_exposure_base):
    """function to calculate the indices 
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value.
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *continent* : continent in which area is situated
        *area* : area to be analyzed
        *degree* : the gridsize at which calculations will take place (given in degrees)
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)   
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on the max of the area as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using max per area")
    
    cisi_exposure = copy.deepcopy(cisi_exposure_base) #to avoid problems later on when cisi_exposure is returned
    #firstly, make indices based on assets to make the conversion to an index per groups/values       
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system]["Index_{}".format(value)] = 0 #create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]: 
                if asset in cisi_exposure[ci_system].columns: #check whether asset in dictioniary exists in cisi exposure geodataframe 
                    cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/cisi_exposure[ci_system][asset].max() #add column km/max km, calculate asset index
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)]*(weight_assets[ci_system][value][asset]) #assetgroup index     
                else:
                    print("\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure dataframes: {}, {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(area, asset))

        #secondly, make indices based on value/groups to make the conversion to an index per subsystem 
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0 #create column in cisi_exposure to calculate the index of the subsystems
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]: 
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)]*(weight_groups[ci_system][value]) #calculate subsystem index

    #lastly, make final exposure index based on the subsystem 
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)
            
    return exposure_index,cisi_exposure

def cisi_mean_per_area(weight_assets, weight_groups, weight_subsystems, continent,area,degree,infrastructure_systems,cisi_exposure_base):
    """function to calculate the indices 
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value.
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *continent* : continent in which area is situated
        *area* : area to be analyzed
        *degree* : the gridsize at which calculations will take place (given in degrees)
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on the mean of the area as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using mean per area")
  
    cisi_exposure = copy.deepcopy(cisi_exposure_base) #to avoid problems later on when cisi_exposure is returned
    #firstly, make indices based on assets to make the conversion to an index per groups/values       
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system]["Index_{}".format(value)] = 0 #create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]: 
                if asset in cisi_exposure[ci_system].columns: #check whether asset in dictioniary exists in cisi exposure geodataframe 
                    #get the mean ignoring zeros
                    temp = copy.deepcopy(cisi_exposure[ci_system][asset])
                    temp[temp == 0] = np.nan
                    cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/temp.mean() #add column km/max km, calculate asset index
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)]*(weight_assets[ci_system][value][asset]) #assetgroup index           
                else:
                    print("\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure dataframes: {}, {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(area, asset))

        #secondly, make indices based on value/groups to make the conversion to an index per subsystem 
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]: 
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)]*(weight_groups[ci_system][value]) #calculate subsystem index

    #lastly, make final exposure index based on the subsystem 
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)
            
    return exposure_index,cisi_exposure
    
def cisi_overall_mean_max(weight_assets, weight_groups, weight_subsystems, continent,area,degree, overall_statistics_tuple,infrastructure_systems,cisi_exposure_base, overall_mean=False):
    """function to calculate the indices #depreciated
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value.
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *continent* : continent in which area is situated
        *area* : area to be analyzed
        *degree* : the gridsize at which calculations will take place (given in degrees)
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
        *overall_mean* : if False, then the overall max will be used, if True, then the overall mean will be used  
        *overall_statistics_tuple*:
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on either the overall max or mean of the area as well as the subscores of each subsystem (columns => score and rows => gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using overall max and/or min")
    
    #check whether overall mean, overall max or both need to be used
    method_list = []
    method_list.append(1) if overall_mean == True else method_list.append(0)
    
    cisi_exposure = copy.deepcopy(cisi_exposure_base) #to avoid problems later on when cisi_exposure is returned
    #firstly, make indices based on assets to make the conversion to an index per groups/values       
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system]["Index_{}".format(value)] = 0 #create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]: 
                if asset in cisi_exposure[ci_system].columns: #check whether asset in dictioniary exists in cisi exposure dataframe                         
                    cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/overall_statistics_tuple[method_list[0]][degree][ci_system][value][asset] #add column km/max km, calculate asset index
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)]*(weight_assets[ci_system][value][asset]) #assetgroup index       
                else:
                    print("\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure geodataframes: {}, {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(area, asset))

        #secondly, make indices based on value/groups to make the conversion to an index per subsystem 
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]: 
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)]*(weight_groups[ci_system][value]) #calculate subsystem index

    #lastly, make final exposure index based on the subsystem 
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)
                                                       
    return exposure_index,cisi_exposure    
    
def overall_statistics_per_asset_dict(areas, weight_assets, degrees, infrastructure_systems, make_histograms=False): #degrees, weight_assets, infrastructure_systems, output_infra_base_gpkg_path):
    """function to calculate the max, mean and minimum values of an asset 
    Arguments:
        *areas*: dictionary with continents as keys and areas/countries as values
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value.
        *degrees* : list with gridsizes at which calculations will take place (given in degrees)
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        
    Returns:
        tuples containing dictionaries:
        - tuple[0] will result in an max dictionary. Maximum values are saved for each asset per given degree
        - tuple[1] will result in an mean dictionary. Mean values are saved for each asset per given degree
        - tuple[2] will result in an min dictionary. Minimum values are saved for each asset per given degree
    """

    #prepare template dictionary 
    asset_dict_temp = copy.deepcopy(weight_assets) #use deepcopying for nested dictionaries https://stackoverflow.com/questions/39474959/nested-dictionaries-copy-or-deepcopy
    for ci_system in asset_dict_temp:
        for value in asset_dict_temp[ci_system]:
            for asset in asset_dict_temp[ci_system][value]:
                asset_dict_temp[ci_system][value][asset]=0
    
    #prepare dictionaries using template  
    overall_max_dict = {degree: copy.deepcopy(asset_dict_temp) for degree in degrees} #prepare max_per_asset dictionary
    overall_mean_dict = {degree: copy.deepcopy(asset_dict_temp) for degree in degrees} #prepare mean_per_asset dictionary
    overall_min_dict = {degree: copy.deepcopy(asset_dict_temp) for degree in degrees} #prepare min_per_asset dictionary

    for degree in degrees:
        for ci_system in infrastructure_systems:
            #create pandas dataframe with assets as columns for subsystem
            temp_df_infra_base_data = pd.DataFrame() #columns = subsystem_asset_list)
            #put data of subsystem per area in one dataframe
            for continent in areas:
                for area in areas[continent]:
                    if os.path.isfile(os.path.join(output_infra_base_gpkg_path,continent,area,'gridsize_{}'.format(degree), '{}_{}.gpkg'.format(area, ci_system))) == True:
                        #print(os.path.join(output_infra_base_gpkg_path,'{}\{}\gridsize_{}'.format(continent,area,degree), '{}_{}.gpkg'.format(area, ci_system)))
                        infra_base_data = (gpd.read_file(os.path.join(output_infra_base_gpkg_path,continent,area,'gridsize_{}'.format(degree), '{}_{}.gpkg'.format(area, ci_system)))).drop(['index'],axis=1) #open grid data and delete index column
                        temp_df_infra_base_data = temp_df_infra_base_data.append(infra_base_data, ignore_index=True, sort=False) #put data of subsystem per area in one dataframe
                        #print(temp_df_infra_base_data)
                    else:
                        print("WARNING: the following basefile does not exist: {}".format(os.path.join(output_infra_base_gpkg_path,continent,area,'gridsize_{}'.format(degree), '{}_{}.gpkg'.format(area, ci_system))))
            
            #get max, mean and min for desired group (see infrastructure_systems), get assets of this group, calculate mean and put in dictionary max_per_asset_dict
            #print("Overview of means of assets")
            for value in infrastructure_systems[ci_system]:
                for asset in overall_mean_dict[degree][ci_system][value]:
                    #check if assets exists in one of the columns 
                    if asset in temp_df_infra_base_data:
                        overall_max_dict[degree][ci_system][value][asset]=temp_df_infra_base_data[asset].max()
                        
                        temp_df_infra_base_data[asset][temp_df_infra_base_data[asset] == 0] = np.nan #prior to calculating mean, replace 0 with nans
                        overall_mean_dict[degree][ci_system][value][asset] = temp_df_infra_base_data[asset].mean() 
                        overall_min_dict[degree][ci_system][value][asset]=temp_df_infra_base_data[asset].min()
                        
                        if make_histograms==True:
                            make_histogram_automatic(ci_system, asset, degree, temp_df_infra_base_data, temp_df_infra_base_data[asset].max(), temp_df_infra_base_data[asset].mean(), temp_df_infra_base_data[asset].min(), output_histogram_path)
                
    return overall_max_dict, overall_mean_dict, overall_min_dict


def final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems):
    """function to calculate CISI
    Arguments:
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value 
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        
    Returns:
         pd containing the final exposure index as well as the subscores of each subsystem (columns => score and rows => the gridcell) 
    """
    #Get a list of columns to be included in final exposure output
    column_names_lst = ['CISI_exposure']#, 'CISI_exposure_unnormalized']
    for ci_system in weight_subsystems:
        column_names_lst.append("Subscore_{}".format(ci_system))  
    column_names_lst.append("geometry")
    
    #Create exposure index dataframe
    exposure_index = cisi_exposure[ci_system][["geometry"]].copy() #create dataframe to save data in by deep copying geometry of one of the subsystems --> consider using .set_index('index') to make index column the index of dataframe 
    exposure_index["CISI_exposure_unnormalized"] = 0 

    #add columns to exposure_index df
    subscore_list = [] #if ci_system needs to be analyzed, save ci_system in subscore list
    for ci_system in weight_subsystems: #loop over each CI subsystem
        #if ci_system in weight_subsystems AND in infrastructure_systems
        if ci_system in infrastructure_systems:
            exposure_index["Subscore_{}".format(ci_system)] = cisi_exposure[ci_system]["Index_{}".format(ci_system)]*(weight_subsystems[ci_system]) #column for subscore
            exposure_index["CISI_exposure_unnormalized"] += exposure_index["Subscore_{}".format(ci_system)] #column for total score 
            subscore_list.append(ci_system)
        #ci_system in weigh_subsystems BUT NOT in infrastructure_systems (i.g. ci_system is not analyzed, while included in weighting)
        else:
            exposure_index["Subscore_{}".format(ci_system)] = np.NaN 
    
    #Normalize score between 0 and 1
    exposure_index["CISI_exposure"] = exposure_index["CISI_exposure_unnormalized"]/exposure_index["CISI_exposure_unnormalized"].max()
    
    #get subscore per infrastructure system 
    for ci_system in subscore_list:
        exposure_index["Subscore_{}".format(ci_system)] = exposure_index["Subscore_{}".format(ci_system)]/exposure_index["CISI_exposure_unnormalized"].max()    
    
    #use column_names_lst to reorder columns and delete exposure_index["CISI_exposure_unnormalized"]
    exposure_index = exposure_index.reindex(columns=column_names_lst) 
    
    return exposure_index


########################################################################################################################
################          Functions for exposure index outputs                ##########################################
########################################################################################################################


def make_histogram_automatic(ci_system, asset, degree, temp_df_infra_base_data, max_value, mean_value, min_value, output_histogram_path):
    """function make histograms of asset distribution
    Arguments:
        *ci_system* : ci_system under which asset is categorized
        *asset* : asset/infrastructure type to be analyzed
        *degree* : gridsize in degrees
        *temp_df_infra_base_data*: dataframe with assets as columns and amount of infrastructure as rows
        *max_value* : Maximum values for given asset per given degree
        *mean_value* : Mean values for given asset per given degree
        *min_value* : Minimum values for given asset per given degree
        *output_histogram_path* (str): directory to output location of histograms
    Returns:
         pd containing the final exposure index as well as the subscores of each subsystem (columns => score and rows => the gridcell) 
    """
    fig, ax = plt.subplots(figsize=(8,4))

    # Draw the plot
    ax.hist(temp_df_infra_base_data[asset], bins = 100,
             color = 'lightsteelblue', edgecolor = 'black', lw=0.5)

    # Title, labels and ticks
    if '_count' in asset:
        ax.set_title('Histogram of asset: {}, {}'.format(asset.replace('_count',''), ci_system), size = 12)
        ax.set_xlabel('Number of assets per grid', size = 10)
    elif '_km2' in asset:
        ax.set_title('Histogram of asset: {}, {}'.format(asset.replace('_km2',''), ci_system), size = 12)
        ax.set_xlabel('Area of asset per grid ($\mathregular{km^2}$)', size = 10)
    elif '_km' in asset:
        ax.set_title('Histogram of asset: {}, {}'.format(asset.replace('_km',''), ci_system), size = 12)
        ax.set_xlabel('Length of asset per grid (km)', size = 10)

    ax.set_ylabel('Frequency', size= 10)
    ax.margins(x=0)

    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_locator(MaxNLocator(integer=True)) # Be sure to only pick integer tick locations
    ax.xaxis.set_minor_locator(AutoMinorLocator()) #see https://matplotlib.org/api/ticker_api.html?highlight=fixedlocator#module-matplotlib.ticker

    # Plot min, max and average line
    plt.axvline(min_value, color='white', linewidth=0, label='minimum: {:5.1f}'.format(min_value))
    plt.axvline(mean_value, color='slategrey', linestyle='dashed', linewidth=2, label='mean: {:12.1f}'.format(mean_value))
    plt.axvline(max_value, color='white', linewidth=0, label='maximum: {:5.1f}'.format(max_value))

    leg = plt.legend(loc='upper right', prop={'size': 9})
    leg.get_frame().set_linewidth(0.0)

    plt.tight_layout()

    plt.savefig(os.path.join(output_histogram_path, 'histogram_gridsize_{}_{}_{}.png'.format(degree, ci_system, asset)), bbox_inches='tight')
    plt.close(fig)  
    
    
def make_plots_automatic(cisi_exposure_output, exposure_index, goal_area, output_path):
    """
    Arguments:
        *cisi_exposure_output*: cisi_exposure with details of indices assets, groups and subsystem
        *exposure_index* : pd containing the final exposure index as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        *goal_area* (str, optional): area that will be analyzed. Defaults to "Global".
        *output_path* : directory to save outputs
    Returns:
        plots for each asset, subsystem, system and final index 
    """
    from shapely.wkb import loads
    from matplotlib.colors import TwoSlopeNorm
    
    #make plots of indices assets, groups and subsystems and save in output_path
    for ci_system in cisi_exposure_output:
        cisi_exposure_output[ci_system]['geometry'] = cisi_exposure_output[ci_system].geometry.apply(lambda x : loads(pygeos.to_wkb(x))) #transform geometry back to shapely geometry
        cisi_exposure_output[ci_system] = gpd.GeoDataFrame(cisi_exposure_output[ci_system], crs="EPSG:4326", geometry='geometry')
        #get limits of grids (https://www.earthdatascience.org/courses/scientists-guide-to-plotting-data-in-python/plot-spatial-data/customize-vector-plots/python-change-spatial-extent-of-map-matplotlib-geopandas/)
        xlim = ([cisi_exposure_output[ci_system]["geometry"].total_bounds[0],  cisi_exposure_output[ci_system]["geometry"].total_bounds[2]])
        ylim = ([cisi_exposure_output[ci_system]["geometry"].total_bounds[1],  cisi_exposure_output[ci_system]["geometry"].total_bounds[3]])

        for col in cisi_exposure_output[ci_system].columns:
            if "Index" in col:
                # plot
                fig, ax = plt.subplots(figsize=(15, 7))
                ax.set_xlim(xlim)
                ax.set_ylim(ylim)

                #to allign color bar with figure
                divider = make_axes_locatable(ax)
                cax = divider.append_axes("right", size="5%", pad=0.1)

                #plot subsystem
                if "Index_{}".format(ci_system) == col:
                    #print("plot subsystem")
                    plt.title("{}: {}, {} (max.={:.3f})".format(ci_system, "Index_{}".format(ci_system), goal_area, cisi_exposure_output[ci_system][col].max()), x=-10)
                    cisi_exposure_output[ci_system].plot(column=col,
                                          cmap='gist_heat_r', 
                                          legend=True,
                                          norm = TwoSlopeNorm(vmin=0, vcenter=0.25, vmax=1),
                                          ax=ax, 
                                          vmax=1, 
                                          cax=cax)

                    plt.savefig(os.path.join(output_path, 'Subsystem_Index_{}.png'.format(ci_system)), bbox_inches='tight')
                    plt.close(fig)

                #plot assets and groups
                else:
                    #print("plot assets and groups")
                    plt.title("{}: {}, {} (max.={:.3f})".format(ci_system, col, goal_area, cisi_exposure_output[ci_system][col].max()), x=-10)
                    cisi_exposure_output[ci_system].plot(column=col,
                                          cmap='gist_heat_r', 
                                          legend=True, 
                                          norm = TwoSlopeNorm(vmin=0, vcenter=0.25, vmax=1),
                                          ax=ax, 
                                          vmax=1, 
                                          cax=cax) #https://gis.stackexchange.com/questions/330008/center-normalize-choropleth-colors-in-geopandas

                    plt.savefig(os.path.join(output_path, '{}_{}.png'.format(ci_system,col)), bbox_inches='tight')
                    plt.close(fig)

    #plot of final_exposure
    exposure_index['geometry'] = exposure_index.geometry.apply(lambda x : loads(pygeos.to_wkb(x))) #transform geometry back to shapely geometry
    exposure_index = gpd.GeoDataFrame(exposure_index, crs="EPSG:4326", geometry='geometry')
    col = "CISI_exposure"
    fig, ax = plt.subplots(figsize=(15,7))

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    #to allign color bar with figure
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    #plot
    plt.title("CISI_exposure, {}".format(goal_area), x=-10)
    exposure_index.plot(column=col,
                          cmap='gist_heat_r', 
                          legend=True,
                          norm = TwoSlopeNorm(vmin=0, vcenter=0.25, vmax=1),
                          ax=ax, 
                          vmax=1, 
                          cax=cax)

    plt.savefig(os.path.join(output_path, 'CISI_exposure.png'), bbox_inches='tight')
    plt.close(fig)
    
def transform_to_gpd(df1):
    """function to transform pygeos format to geopandas
    Arguments:
        *df1* : dataframe with pygeos coordinates
    Returns:
         df with shapely coordinates
    """
    from shapely.wkb import loads
    temp_df = df1.copy()
    temp_df['geometry'] = temp_df.geometry.apply(lambda x : loads(pygeos.to_wkb(x))) #transform geometry back to shapely geometry
    temp_df = gpd.GeoDataFrame(temp_df, crs="EPSG:4326", geometry='geometry')
    
    return temp_df
        
def get_documentation(areas, infrastructure_systems, degrees, weight_assets, weight_groups, weight_subsystems, overall_statistics_tuple, output_documentation_path, test_number):
    with open(os.path.join(output_documentation_path,"documentation_{}.txt".format(test_number)), 'w+') as f:
        f.write("This file contains documentation on the exposure index: \n\
        - the areas that are analyzed\n\
        - the gridsizes \n\
        - the the subsystems, groups and assets that are analyzed and weighting used to calculate the exposure index\n\
        - the max count/length/area of each asset \n\
        - the mean count/length/area of each asset \n\
        ---------------------------------------------------------------------------------------------------------")

        f.write("\n\n\nOverview of areas that are analyzed: \n\
        {}".format(areas))

        f.write("\n\n\nOverview of subsystems, groups and assets that are analyzed: \n\
        {}".format(infrastructure_systems))

        f.write("\n\n\nOverview of size of grids in degrees: \n\
        {}".format(degrees))

        f.write("\n\n\nOverview of the weightings: \n\
        weightings of assets: \n\
        {} \n\n\
        weightings of groups: \n\
        {} \n\n\
        weightings of subsystems: \n\n\
        {}".format(weight_assets, weight_groups, weight_subsystems))

        for degree in degrees:
            f.write("\n\n\nFor index calculations when the gridsize is {} degrees".format(degree))

            f.write("\n\nOverview of the max count/length/area of each asset: \n\
            {}".format(overall_statistics_tuple[0][degree]))

            f.write("\n\nOverview of the mean count/length/area of each asset: \n\
            {}".format(overall_statistics_tuple[1][degree]))

            f.write("\n\nOverview of the min count/length/area of each asset: \n\
            {}".format(overall_statistics_tuple[2][degree]))

        f.close()    