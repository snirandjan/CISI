"""
Transform vector data to raster

@Author: Sadhana Nirandjan - Institute for Environmental studies, VU University Amsterdam
"""
################################################################
                ## Load package and set path ##
################################################################
import os,sys
import pygeos
import math
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import rasterio
import geocube
import georasters
from rasterio.plot import show
from pathlib import Path
from pgpkg import Geopackage
from shapely.wkb import loads
from geopandas import GeoDataFrame
from mpl_toolkits.axes_grid1 import make_axes_locatable
#pip install geofeather
from geofeather.pygeos import to_geofeather, from_geofeather
from shapely.wkb import loads
from osgeo import gdal

sys.path.append("C:\Projects\Coastal_Infrastructure\scripts")
import cisi
import cisi_exposure
import extract
import gridmaker

####################################################
#Load data#
####################################################
#set pathways
#base_path = os.path.abspath('C:/Users/snn490/surfdrive/Outputs/Exposure/CISI_Netherlands_correct') #this path contains all data that's needed as input and will contain directories to export outputs
base_path = os.path.abspath(os.path.join('/scistor','ivm', 'snn490', 'Outputs', 'Exposure', 'Final_cisi_files')) #this path contains all data that's needed as input and will contain directories to export outputs

# Set path to inputdata
#data_path = os.path.abspath(os.path.join(base_path, 'Infrastructure_base')) #path to map with infra-gpkg's 
data_path = os.path.abspath(os.path.join(base_path, 'CISI','025_degree')) #path to map with infra-gpkg's 

# create extra pathway
if os.path.isdir((os.path.abspath(os.path.join(data_path, 'temp')))) == False:
    Path(os.path.abspath(os.path.join(data_path, 'temp'))).mkdir(parents=True, exist_ok=True)

####################################################
#Set variables#
####################################################
files = ['africa', 'asia', 'central_america', 'europe','north_america','oceania','south_america', 'global']

####################################################
#transform CISI-files to geotiff#
####################################################
for file in files:
    # prepare data
    print('Import data for file {}'.format(file))
    df = from_geofeather(os.path.join(data_path, 'CISI_{}.feather'.format(file)))

    # prepare dataframe
    df['geometry']=pygeos.centroid(df.geometry)
    gdf = cisi_exposure.transform_to_gpd(df) #transform geometry back to shapely geometry and gpd

    print('Time to create a sub dataset for {}'.format(file))
    # create subset in xyz format
    sub_data = {'x': gdf['geometry'].x.tolist(),
               'y': gdf['geometry'].y.tolist(),
               'z': gdf['CISI'].tolist()
            }

    sub_gdf = pd.DataFrame (sub_data, columns = ['x','y','z'])
    sub_gdf = sub_gdf.sort_values(by=['y','x'], ascending = [False,True])

    #see: https://www.youtube.com/watch?v=zLNLG0j13Cw
    if os.path.exists("sub_gdf.csv"):
        os.remove("sub_gdf.csv")
    sub_gdf.to_csv("sub_gdf.csv", index = False) # create

    if os.path.exists(os.path.abspath(os.path.join(data_path, "temp","sub_gdf_{}.vrt".format(file)))):
        os.remove(os.path.abspath(os.path.join(data_path, "temp","sub_gdf_{}.vrt".format(file))))

    f = open(os.path.abspath(os.path.join(data_path, "temp", "sub_gdf_{}.vrt".format(file))), "w")
    f.write("<OGRVRTDataSource>\n \
        <OGRVRTLayer name=\"sub_gdf\">\n \
            <SrcDataSource>sub_gdf.csv</SrcDataSource>\n \
            <GeometryType>wkbPoint</GeometryType>\n \
            <GeometryField encoding=\"PointFromColumns\" x=\"x\" y=\"y\" z=\"z\"/>\n \
        </OGRVRTLayer>\n \
    </OGRVRTDataSource>")
    f.close()

    r = gdal.Rasterize(os.path.abspath(os.path.join(data_path, "{}.tif".format(file))), os.path.abspath(os.path.join(data_path, "temp", "sub_gdf_{}.vrt".format(file))), outputSRS = "EPSG:4326", xRes = 0.250000, yRes= 0.250000, attribute = "z", noData=np.nan)
    r = None




####################################################
#Load data#
####################################################
#set pathways
#base_path = os.path.abspath('C:/Users/snn490/surfdrive/Outputs/Exposure/CISI_Netherlands_correct') #this path contains all data that's needed as input and will contain directories to export outputs
base_path = os.path.abspath(os.path.join('/scistor','ivm', 'snn490', 'Outputs', 'Exposure', 'Final_cisi_files')) #this path contains all data that's needed as input and will contain directories to export outputs

# Set path to inputdata
#data_path = os.path.abspath(os.path.join(base_path, 'Infrastructure_base')) #path to map with infra-gpkg's 
data_path = os.path.abspath(os.path.join(base_path, 'Amount_of_infrastructure','025_degree')) #path to map with infra-gpkg's 

# create extra pathway
if os.path.isdir((os.path.abspath(os.path.join(data_path, 'temp')))) == False:
    Path(os.path.abspath(os.path.join(data_path, 'temp'))).mkdir(parents=True, exist_ok=True)

####################################################
#Set variables#
####################################################
weight_assets = {"energy": {"power": {"line_km": 1/7,"minor_line_km": 1/7,"cable_km": 1/7,"plant_km2": 1/7,"substation_km2": 1/7,
                                        "power_tower_count": 1/7,"power_pole_count":1/7}}, 
                "transportation": {"roads":  {"primary_km": 1/3, "secondary_km": 1/3 , "tertiary_km": 1/3}, 
                                    "airports": {"airports_km2": 1},
                                    "railways": {"railway_km": 1}},
                                    #"ports": {"industrial_km2": 1/3, "harbour_km2": 1/3, "port_km2": 1/3}},
                "water": {"water_supply": {"water_tower_km2": 1/5, "water_well_km2": 1/5, "reservoir_covered_km2": 1/5,
                                            "water_works_km2": 1/5, "reservoir_km2": 1/5}},
                "waste": {"waste_solid": {"landfill_km2": 1/2,"waste_transfer_station_km2": 1/2},
                        "waste_water": {"wastewater_treatment_plant_km2": 1}},
                "telecommunication": {"telecom": {"communication_tower_count": 1/2, "mast_count": 1/2}},
                "healthcare": {"health": {"clinic_count": 1/12, "doctors_count": 1/12, "hospital_count": 1/12, "dentist_count": 1/12, "pharmacy_count": 1/12, 
                            "physiotherapist_count" : 1/12, "alternative_count" : 1/12, "laboratory_count" : 1/12, "optometrist_count" : 1/12, "rehabilitation_count" : 1/12, 
                            "blood_donation_count" : 1/12, "birthing_center_count" : 1/12}},
                "education": {"education_facilities": {"college_km2": 1/5, "kindergarten_km2": 1/5, "library_km2": 1/5, "school_km2": 1/5, "university_km2": 1/5}}
                }

#####################################################
#transform amount of infrastructure files to geotiff#
#####################################################
for ci_system in weight_assets:
    # prepare data
    print('Import data for ci system {}'.format(ci_system))
    df = from_geofeather(os.path.join(data_path, 'summary_{}.feather'.format(ci_system)))

    # prepare dataframe
    df['geometry']=pygeos.centroid(df.geometry)
    gdf = cisi_exposure.transform_to_gpd(df) #transform geometry back to shapely geometry and gpd

    for ci_subsystem in weight_assets[ci_system]:
        for infrastructure_type in weight_assets[ci_system][ci_subsystem]:
            print('Time to create a sub dataset for {}'.format(infrastructure_type))
            # create subset in xyz format
            sub_data = {'x': gdf['geometry'].x.tolist(),
                       'y': gdf['geometry'].y.tolist(),
                       'z': gdf[infrastructure_type].tolist()
                    }

            sub_gdf = pd.DataFrame (sub_data, columns = ['x','y','z'])
            sub_gdf = sub_gdf.sort_values(by=['y','x'], ascending = [False,True])

            #see: https://www.youtube.com/watch?v=zLNLG0j13Cw
            if os.path.exists("sub_gdf.csv"):
                os.remove("sub_gdf.csv")
            sub_gdf.to_csv("sub_gdf.csv", index = False) # create

            if os.path.exists(os.path.abspath(os.path.join(data_path, "temp","sub_gdf_{}.vrt".format(infrastructure_type)))):
                os.remove(os.path.abspath(os.path.join(data_path, "temp","sub_gdf_{}.vrt".format(infrastructure_type))))

            f = open(os.path.abspath(os.path.join(data_path, "temp", "sub_gdf_{}.vrt".format(infrastructure_type))), "w")
            f.write("<OGRVRTDataSource>\n \
                <OGRVRTLayer name=\"sub_gdf\">\n \
                    <SrcDataSource>sub_gdf.csv</SrcDataSource>\n \
                    <GeometryType>wkbPoint</GeometryType>\n \
                    <GeometryField encoding=\"PointFromColumns\" x=\"x\" y=\"y\" z=\"z\"/>\n \
                </OGRVRTLayer>\n \
            </OGRVRTDataSource>")
            f.close()

            if '_count' in infrastructure_type:
                infrastructure_type_short = '{}'.format(infrastructure_type.replace('_count',''))
            if '_km' in infrastructure_type:
                infrastructure_type_short = '{}'.format(infrastructure_type.replace('_km',''))
            if '_km2' in infrastructure_type:
                infrastructure_type_short = '{}'.format(infrastructure_type.replace('_km2',''))

            r = gdal.Rasterize(os.path.abspath(os.path.join(data_path, "{}.tif".format(infrastructure_type_short))), os.path.abspath(os.path.join(data_path, "temp", "sub_gdf_{}.vrt".format(infrastructure_type))), outputSRS = "EPSG:4326", xRes = 0.100000, yRes= 0.10000, attribute = "z", noData=np.nan)
            r = None