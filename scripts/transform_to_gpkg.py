################################################################
                ## Load package and set path ##
################################################################
import os,sys
import pygeos
import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
#from pgpkg import Geopackage
#pip install openpyxl
from geofeather.pygeos import to_geofeather, from_geofeather
from itertools import repeat
from osgeo import gdal 
gdal.SetConfigOption("OSM_CONFIG_FILE", os.path.join("..", "osmconf.ini"))

#sys.path.append("C:\Projects\Coastal_Infrastructure\scripts")
import cisi_exposure
import extract
import gridmaker
import cisi
from multiprocessing import Pool,cpu_count

################################################################
                ## Transform to gpkg ##
################################################################

# Specify which subsystems and associated asset groups need to be analyzed
infrastructure_systems = {
                    "energy":["power"], 
                    "transportation": ["roads", "airports","railways"],
                    "water":["water_supply"],
                    "waste":["waste_solid","waste_water"], 
                    "telecommunication":["telecom"],
                    "healthcare": ["health"], #'health_point']#['health_polygon']#,
                    "education":["education_facilities"]
                    }

#path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','CISI_BeNeLux','Infrastructure_base','base_per_area'))

#for method in ['method_max']:
#    path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','CISI_Oceania', 'index',method))
#    temp_py = from_geofeather(os.path.join(path, 'CISI_exposure_Oceania.feather'))                                            
#    temp_df = cisi_exposure.transform_to_gpd(temp_py) #transform df to gpd with shapely geometries
#    temp_df.to_file(os.path.join(path, 'CISI_exposure_Oceania.gpkg'), layer=' ', driver="GPKG")

#for ci_system in infrastructure_systems:
#    path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs'))
#    temp_py = from_geofeather(os.path.join(path, 'summary_basecalcs_{}.feather'.format(ci_system)))                                            
#    temp_df = cisi_exposure.transform_to_gpd(temp_py) #transform df to gpd with shapely geometries
#    temp_df.to_file(os.path.join(path, 'summary_basecalcs_{}.gpkg'.format(ci_system)), layer=' ', driver="GPKG")

area_list = ['Europe', 'Africa', 'Asia', 'Central-America', 'North-America', 'Oceania', 'South-America']#, 'Global'] #, 

for area in area_list: 
    path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','CISI_files', '010'))
    temp_py = from_geofeather(os.path.join(path, 'CISI_{}.feather'.format(area)))                                            
    temp_df = cisi_exposure.transform_to_gpd(temp_py) #transform df to gpd with shapely geometries
    temp_df.to_file(os.path.join(path, 'CISI_{}.gpkg'.format(area)), layer=' ', driver="GPKG")

#path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','CISI_global', 'index_010','method_max', 'non_normalized'))
#temp_py = from_geofeather(os.path.join(path, 'CISI_exposure_Global.feather'))                                            
#temp_df = cisi_exposure.transform_to_gpd(temp_py) #transform df to gpd with shapely geometries
#temp_df.to_file(os.path.join(path, 'CISI_exposure_Global.gpkg'), layer=' ', driver="GPKG")

#path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','CISI_Africa_025degree_cluster','Infrastructure_base'))
#for ci_system in infrastructure_systems:
#    temp_py = from_geofeather(os.path.join(path, 'summary_basecalcs_{}.feather'.format(ci_system)))                                            
#    temp_df = cisi_exposure.transform_to_gpd(temp_py) #transform df to gpd with shapely geometries
#    temp_df.to_file(os.path.join(path, 'summary_basecalcs_{}.gpkg'.format(ci_system)), layer=' ', driver="GPKG")#


################################################################
                ## make grid for specific area ##
################################################################

##grid_data = gpd.read_file(os.path.join(os.path.abspath(os.path.join('C:/Users/snn490/surfdrive','Outputs','Grid_data')),'global_grid_1degree.gpkg')) #open as geofeather
#grid_data = from_geofeather(os.path.join('/scistor','ivm','snn490','Outputs','Grid_data','global_grid_025.geofeather')) #open as geofeather
#shape = gpd.read_file(os.path.join('/scistor','ivm','snn490','Datasets','Administrative_boundaries', 'boundaries','Simplified_countries.shp'))
#glob_info = pd.read_excel(os.path.join('/scistor','ivm','snn490','Datasets','global_information_advanced.xlsx'))

##for continent; hard cut
##continent_lst = glob_info['continent'].unique()
#continent_lst = ['Europe', 'North-America']
#for continent in continent_lst:
#    continent_countries = glob_info[glob_info['continent'] == continent] #get details all countries of continent
#    continent_countries_lst = list(continent_countries['ISO_3digit'].unique()) #put in list
#    df_shapefiles_continents = pd.DataFrame()
#    for country_code in continent_countries_lst:
#        if df_shapefiles_continents.empty == True:
#            df_shapefiles_continents = pd.merge(df_shapefiles_continents, shape.loc[shape['ISO'] == country_code], how='outer', left_index=True, right_index=True)
#        else:
#            df_shapefiles_continents = df_shapefiles_continents.append(shape.loc[shape['ISO'] == country_code], ignore_index=True, sort=False)
#            df_shapefiles_continents_py = pd.DataFrame(df_shapefiles_continents) 
#    df_shapefiles_continents_py['geometry'] = pygeos.from_shapely(df_shapefiles_continents_py.geometry) #transform geometry to be able to make output
# 
#    spat_tree = pygeos.STRtree(grid_data.geometry) # https://pygeos.readthedocs.io/en/latest/strtree.html
#    
#    print('Time to merge data for {}'.format(continent))
#    merged_geometry = pygeos.set_operations.union_all(df_shapefiles_continents_py.geometry) #merge shapefiles
#    df_shapefiles_continents_py_all = pd.DataFrame([merged_geometry], columns = ['geometry']) 
#    
#    grid_data_area = (grid_data.loc[spat_tree.query(df_shapefiles_continents_py_all.geometry.iloc[0],predicate='intersects').tolist()])#.sort_index(ascending=True) #get grids that overlap with cover_box
#    grid_data_area = grid_data_area.reset_index(drop=True)#.rename(columns = {'index':'grid_number'}) #get index as column and name column grid_number
#    
#    print('Time to output data for {}'.format(continent))
#    to_geofeather(grid_data_area, os.path.join('/scistor','ivm','snn490','Outputs','Grid_data', '{}_025degree.geofeather'.format(continent)), crs="EPSG:4326") #save as geofeather
#    temp_df = cisi_exposure.transform_to_gpd(grid_data_area) #transform df to gpd with shapely geometries
#    temp_df.to_file(os.path.join('/scistor','ivm','snn490','Outputs','Grid_data', '{}_025degree.gpkg'.format(continent)), layer=' ', driver="GPKG")


################################################################
                ## Replace 0's with NaN's##
################################################################

#open gpkg
#path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','test_2020','025_degree','CISI_Europe_025degree', 'index','method_max'))
#gdf = gpd.read_file(os.path.join(path, 'CISI_exposure_Europe.gpkg'))   
#gdf.replace(0, np.nan, inplace=True) #make NaN of all 0's
#df = pd.DataFrame(gdf)

#df.to_file(os.path.join(path, 'CISI_exposure_Europe_nan.gpkg'), layer=' ', driver="GPKG")#save again





