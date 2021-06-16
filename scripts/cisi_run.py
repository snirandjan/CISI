################################################################
                ## Load package and set path ##
################################################################
import os,sys
import pygeos
import pandas as pd
import geopandas as gpd
from pathlib import Path
#from pgpkg import Geopackage
from geofeather.pygeos import to_geofeather, from_geofeather
from itertools import repeat
from osgeo import gdal 
gdal.SetConfigOption("OSM_CONFIG_FILE", os.path.join("..", "osmconf.ini"))

#sys.path.append("C:\Projects\Coastal_Infrastructure\scripts")
import cisi
import cisi_exposure
import extract
import gridmaker
from multiprocessing import Pool,cpu_count
                
#def run_all(goal_area = 'Netherlands', local_path = 'C:/Users/snn490/surfdrive'):
def run_all(areas, goal_area = 'Global', local_path = os.path.join('/scistor','ivm','snn490')):
    """Function to manage and run the model (in parts). 

    Args:
        *areas* ([str]): list with areas (e.g. list of countries)
        *goal_area* (str, optional): area that will be analyzed. Defaults to "Global". 
        *local_path* ([str], optional): Local pathway. Defaults to os.path.join('/scistor','ivm','snn490').
    """    

    #extract_infrastructure(local_path)
    #base_calculations(local_path) 
    base_calculations_global(local_path) #if base calcs per area already exist
    cisi_calculation(local_path,goal_area)

################################################################
                    ## set variables ##
################################################################
 
def set_variables():
    """Function to set the variables that are necessary as input to the model

    Returns:
        *infrastructure_systems* (dictionary): overview of overarching infrastructure sub-systems as keys and a list with the associated sub-systems as values 
        *weight_assets* (dictionary): overview of the weighting of the assets per overarching infrastructure sub-system
        *weight_groups* (dictionary): overview of the weighting of the groups per overarching infrastructure sub-system
        *weight_subsystems* (dictionary): overview of the weighting of the sub-systems
    """    
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

    ## Set the weights of all of the infrastructure components
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

    weight_groups = {"energy": {"power": 1}, 
                "transportation": {"roads":  1/3, 
                                    "airports": 1/3,
                                    "railways": 1/3},
                "water": {"water_supply": 1},
                "waste": {"waste_solid": 1/2,
                        "waste_water": 1/2},
                "telecommunication": {"telecom": 1},
                "healthcare": {"health": 1},
                "education": {"education_facilities": 1}
                }

    weight_subsystems = {"energy": 1/7, 
                    "transportation": 1/7,
                    "water": 1/7,
                    "waste": 1/7,
                    "telecommunication": 1/7,
                    "healthcare": 1/7,
                    "education": 1/7
                    }

    return [infrastructure_systems,weight_assets,weight_groups,weight_subsystems]


################################################################
                    ## Set pathways ##
################################################################

def set_paths(local_path = 'C:/Data/CISI',extract_data=False,base_calculation=False,cisi_calculation=False):
    """Function to specify required pathways for inputs and outputs

    Args:
        *local_path* (str, optional): local path. Defaults to 'C:/Data/CISI'.
        *extract_data* (bool, optional): True if extraction part of model should be activated. Defaults to False.
        *base_calculation* (bool, optional): True if base calculations part of model should be activated. Defaults to False.
        *cisi_calculation* (bool, optional): True if CISI part of model should be activated. Defaults to False.

    Returns:
        *osm_data_path* (str): directory to osm data
        *fetched_infra_path* (str): directory to output location of the extracted infrastructure data 
        *country_shapes_path* (str): directory to dataset with administrative boundaries (e.g. of countries)
        *grid_path* (str): directory to feather file of consistent spatial grids
        *infra_base_path* (str): directory to output location of the rasterized infrastructure data 
        *method_max_path* (str): directory to output location of the CISI based on the max of each asset
        *method_mean_path* (str): directory to output location of the CISI based on the mean of the mean of a each asset
    """ 
    # Set path to inputdata
    #osm_data_path = os.path.abspath(os.path.join(local_path,'Datasets','OpenStreetMap')) #path to map with pbf files from OSM 
    osm_data_path = os.path.abspath(os.path.join('/scistor','ivm','data_catalogue','open_street_map','country_osm')) #path to map with pbf files from OSM at cluster
    #grid_file = 'Holland_0.1degree.geofeather' #'global_grid_0_1.geofeather' #name of grid file 
    #grid_file = 'global_grid_0_1.geofeather' #'global_grid_0_1.geofeather' #name of grid file 
    #grid_file = 'North-America_025degree.geofeather' #'global_grid_0_1.geofeather' #name of grid file 
    grid_file = 'global_grid_025.geofeather'
    #grid_file = 'global_grid_010degree.geofeather'
    grid_path = os.path.abspath(os.path.join(local_path,'Outputs','Grid_data',grid_file)) #grid data
    shapes_file = 'global_countries_advanced.geofeather'
    country_shapes_path = os.path.abspath(os.path.join(local_path,'Datasets','Administrative_boundaries', 'global_countries_buffer', shapes_file)) #shapefiles with buffer around country


    # Set path for outputs 
    base_path = os.path.abspath(os.path.join(local_path, 'Outputs', 'Exposure', 'CISI_global')) #this path will contain folders in which 

    # path to save outputs - automatically made, not necessary to change output pathways
    fetched_infra_path = os.path.abspath(os.path.join(base_path,'Fetched_infrastructure')) #path to map with fetched infra-gpkg's 
    #fetched_infra_path = os.path.abspath(os.path.join('C:/Users/snn490/Documents','Fetched_infrastructure')) #path to map with fetched infra-gpkg's TEMPORARY
    infra_base_path = os.path.abspath(os.path.join(base_path, 'Infrastructure_base_025')) #save interim calculations
    method_max_path = os.path.abspath(os.path.join(base_path, 'index_025', 'method_max')) #save figures 
    method_mean_path = os.path.abspath(os.path.join(base_path, 'index_025', 'method_mean')) #save figures 
    #output_documentation_path = os.path.abspath(os.path.join(base_path, 'index', test_number)) #save documentation
    #output_histogram_path = os.path.abspath(os.path.join(base_path, 'index', test_number)) #save documentation

    #Create folders for outputs (GPKGs and pngs)
    #Path(output_histogram_path).mkdir(parents=True, exist_ok=True)
    Path(fetched_infra_path).mkdir(parents=True, exist_ok=True)

    if extract_data:
        return [osm_data_path,fetched_infra_path,country_shapes_path]

    if base_calculation:
        return [grid_path,fetched_infra_path,infra_base_path,country_shapes_path]

    if cisi_calculation:
        return [method_max_path,method_mean_path,infra_base_path]

################################################################
 ## Step 1: Extract requested infrastructure from pbf-file  ##
################################################################

def extract_infrastructure_per_area(area,groups_list,osm_data_path,fetched_infra_path,country_shapes_path):
    """function to extract infrastrastructure for an area 

    Args:
        *area* (str): area to be analyzed
        *osm_data_path* (str): directory to osm data
        *fetched_infra_path* (str): directory to output location of the extracted infrastructure data 
        *country_shapes_path* (str): directory to dataset with administrative boundaries (e.g. of countries)
    """
    #try:
    #get shape data
    shape_countries = from_geofeather(country_shapes_path) #open as geofeather

    fetched_data_dict = {group: pd.DataFrame() for group in groups_list} #Create dictionary with asset groups as keys and df as value
    print("\033[1mTime to extract infrastructure data for area: {}\033[0m".format(area))
    for group in groups_list:
        print("Infrastructure belonging to the group '{}' will now be extracted for {}".format(group, area))
        data = '{}.osm.pbf'.format(area) #make directory to data
        if group == 'power':
            fetched_data_area = extract.merge_energy_datatypes(os.path.join(osm_data_path, data)) #extract required data
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase charachters
        elif group == 'roads':
            fetched_data_area = extract.roads_all(os.path.join(osm_data_path, data)) #extract required data
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase charachters
                list_of_highway_assets_to_keep =["living_street", "motorway", "motorway_link", "primary","primary_link", "residential","road", "secondary", "secondary_link","tertiary","tertiary_link", "trunk", "trunk_link","unclassified","service"]
                fetched_data_area = fetched_data_area.loc[fetched_data_area.asset.isin(list_of_highway_assets_to_keep)].reset_index()
                #reclassify assets 
                mapping_dict = {
                    "living_street" : "tertiary", 
                    "motorway" : "primary", 
                    "motorway_link" : "primary", 
                    "primary" : "primary", 
                    "primary_link" : "primary", 
                    "residential" : "tertiary",
                    "road" : "secondary", 
                    "secondary" : "secondary", 
                    "secondary_link" : "secondary", 
                    "tertiary" : "tertiary", 
                    "tertiary_link" : "tertiary", 
                    "trunk" : "primary",
                    "trunk_link" : "primary",
                    "unclassified" : "tertiary", 
                    "service" : "tertiary"
                }
                fetched_data_area['asset'] = fetched_data_area.asset.apply(lambda x : mapping_dict[x])  #reclassification
        elif group == 'airports':
            fetched_data_area = extract.airports(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                #reclassify assets 
                mapping_dict = {
                    "aerodrome" : "airports",
                }
                fetched_data_area['asset'] = fetched_data_area.asset.apply(lambda x : mapping_dict[x])  #reclassification
                fetched_data_area['geometry'] =pygeos.buffer(fetched_data_area.geometry,0) #avoid intersection
        elif group == 'railways':
            fetched_data_area = extract.railway_all(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                list_of_railway_assets_to_keep =['rail','tram','subway','construction','funicular','light_rail','narrow_gauge']
                fetched_data_area = fetched_data_area.loc[fetched_data_area.asset.isin(list_of_railway_assets_to_keep)].reset_index()
                #reclassify assets 
                mapping_dict = {
                    "rail" : "railway",
                    "tram" : "railway",
                    "subway" : "railway",
                    "construction" : "railway",
                    "funicular" : "railway",
                    "light_rail" : "railway",
                    "narrow_gauge" : "railway",
                    "monorail" : "railway",
                }
                fetched_data_area['asset'] = fetched_data_area.asset.apply(lambda x : mapping_dict[x])  #reclassification   
        elif group == 'ports':
            fetched_data_area  = extract.ports(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                fetched_data_area['geometry'] =pygeos.buffer(fetched_data_area.geometry,0) #avoid intersection
        elif group == 'water_supply':
            fetched_data_area  = extract.water_supply(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                fetched_data_area['geometry'] =pygeos.buffer(fetched_data_area.geometry,0) #avoid intersection
        elif group == 'waste_solid':
            fetched_data_area  = extract.waste_solid(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters  
                fetched_data_area['geometry'] =pygeos.buffer(fetched_data_area.geometry,0) #avoid intersection             
        elif group == 'waste_water':
            fetched_data_area  = extract.waste_water(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                #reclassify assets 
                mapping_dict = {
                    "wastewater_plant" : "wastewater_treatment_plant"
                }
                fetched_data_area['asset'] = fetched_data_area.asset.apply(lambda x : mapping_dict[x])  #reclassification                
                fetched_data_area['geometry'] =pygeos.buffer(fetched_data_area.geometry,0) #avoid intersection
        elif group == 'telecom':
            fetched_data_area  = extract.telecom(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                #reclassify assets 
                mapping_dict = {
                    "communications_tower" : "communication_tower", #big tower
                    "tower" : "communication_tower", #small tower
                    "mast" : "mast"
                }
                fetched_data_area['asset'] = fetched_data_area.asset.apply(lambda x : mapping_dict[x])  #reclassification
        elif group == 'health':
            fetched_data_area  = extract.social_infrastructure_combined(os.path.join(osm_data_path, data))
            if 'asset' in fetched_data_area.columns:
                fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                #reclassify assets 
                #mapping_dict = {
                #    "doctors" : "doctors",
                #    "clinic" : "clinic",
                #    "hospital" : "hospital",
                #    "dentist" : "dentist",
                #    "pharmacy" : "pharmacy",
                #    "physiotherapist" : "others",
                #    "alternative" : "others",
                #    "laboratory" : "others",
                #    "optometrist" : "others",
                #    "rehabilitation" : "others",
                #    "blood_donation" : "others",
                #    "birthing_center" : "others"
                #}
                #fetched_data_area['asset'] = fetched_data_area.asset.apply(lambda x : mapping_dict[x])  #reclassification
        elif group == 'education_facilities':
                fetched_data_area  = extract.education(os.path.join(osm_data_path, data))
                if 'asset' in fetched_data_area.columns:
                    fetched_data_area['asset'] = list(map(lambda x: x.lower(), fetched_data_area['asset'])) #make sure that asset column is in lowercase characters
                    fetched_data_area['geometry'] =pygeos.buffer(fetched_data_area.geometry,0) #avoid intersection
        else:
            print("WARNING: No extracting codes are written for the following area and group: {} {}".format(area, group))

        #get rid of random floating data
        country_shape = shape_countries[shape_countries['ISO_3digit'] == area]
        if country_shape.empty == False: #if ISO_3digit in shape_countries
            spat_tree = pygeos.STRtree(fetched_data_area.geometry)
            fetched_data_area = cisi.clip_pygeos(fetched_data_area,country_shape.iloc[0],spat_tree)
        else:
            print("ISO_3digit code not specified in file containing shapefiles of country boundaries. Floating data will not be removed for area '{}'".format(area))
            
        #Save data in df
        fetched_data_dict[group] = fetched_data_dict[group].append(fetched_data_area, ignore_index=True)
        
    #if all df's are empty for area, then warning. Otherwise, make outputs
    if cisi.check_dfs_empty(fetched_data_dict) == False: #df's contain data
        for group in groups_list:
            #export when df is not empty 
            if fetched_data_dict[group].empty == False:
                print("Extraction of requested infrastructure is complete for group '{}' in area '{}'. This data will now be exported as geofeather...".format(group, area))
                #Export fetched exposure data as geopackage
                temp_df = cisi_exposure.transform_to_gpd(fetched_data_dict[group])
                temp_df.to_file(os.path.join(fetched_infra_path, '{}_{}.gpkg'.format(area,group)), layer=' ', driver="GPKG")
                #with Geopackage(os.path.join(fetched_infra_path, '{}_{}.gpkg'.format(area,group)), 'w') as out:
                #    out.add_layer(fetched_data_dict[group], name=' ', crs='EPSG:4326')
                to_geofeather(fetched_data_dict[group], os.path.join(fetched_infra_path, '{}_{}.feather'.format(area, group)), crs="EPSG:4326") #save as geofeather
            else:
                print("NOTIFICATION: Extraction for group '{}' for area '{}' resulted in an empty df. No output will be made...".format(group, area)) 
    else:
        print("WARNING: No infrastructure data is found in area '{}'. Please check if OSM-file is correct and whether it intersects with polygon of area (country_shape)".format(area))

    #except Exception as e:
    #    print('ERROR: {} for {}'.format(e, area))


def group_infrastructure_assets(infrastructure_systems):
    """function to obtain a list of the infrastructure groups that will be analyzed 

    Args:
        *infrastructure_systems*: dictionary, overview of overarching infrastructure sub-systems as keys and a list with the associated sub-systems as values 

    Returns:
        *groups_list*: list of the infrastructure groups that will be analyzed
    """   
    groups_list = []
    for ci_system in infrastructure_systems:
        for group in infrastructure_systems[ci_system]:
            groups_list.append(group)

    return groups_list

def extract_infrastructure(local_path):
    """function to extract infrastructure per area, parallel processing 

    Args:
        *local_path*: Local pathway. Defaults to os.path.join('/scistor','ivm','snn490').
    """
    # get paths
    osm_data_path,fetched_infra_path,country_shapes_path = set_paths(local_path,extract_data=True)

    # get settings
    infrastructure_systems = set_variables()[0]

    # get all asset groups in a list, so dictionary can be created with asset groups as keys and df as value
    groups_list = group_infrastructure_assets(infrastructure_systems)

    # turn dict into list to make sure we have all unique areas
    #listed_areas = list(areas.values())[0]

    # run the extract parallel per area
    print('Time to start extraction of requested assets for the following areas: {}'.format(areas))
    with Pool(cpu_count()-1) as pool: 
        pool.starmap(extract_infrastructure_per_area,zip(areas,
                                                        repeat(groups_list,len(areas)),
                                                        repeat(osm_data_path,len(areas)),
                                                        repeat(fetched_infra_path,len(areas)),
                                                        repeat(country_shapes_path,len(areas))),
                                                        chunksize=1) 
    

################################################################
      ## Step 2: Perform base calculations per area ##
################################################################

def base_calculation_per_area(area,infrastructure_systems,local_path):
    """calculate the amount of infrastructure per defined area
    Args:
        *area* : area to be analyzed
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values 
        *local_path*: Local pathway. Defaults to os.path.join('/scistor','ivm','snn490'). 
    """
    #try:
    # get paths
    grid_path,fetched_infra_path,infra_base_path,country_shapes_path= set_paths(local_path,base_calculation=True)

    # get grid data
    grid_data = from_geofeather(grid_path) #open as geofeather

    # get all asset groups in a list, so dictionary can be created with asset groups as keys and df as value
    groups_list = group_infrastructure_assets(infrastructure_systems)

    ##check whether base calculations for area already exist
    #check_list = []
    #for ci_system in infrastructure_systems: check_list.append(os.path.isfile(os.path.join(infra_base_path, "base_per_area", '{}_{}.feather'.format(area, ci_system))))
    #if True in check_list: #if at least one base calculation file of area exist, then import data 
    #   print('Base calculations have been performed for "{}". Time to import the base calculation-files.'.format(area))

    #    #import files 
    #    cisi_exposure_base_area = {}
    #    for ci_system in infrastructure_systems:
    #        if os.path.isfile(os.path.join(infra_base_path, "base_per_area", '{}_{}.feather'.format(area, ci_system))) == True:
    #            grid_data_area = from_geofeather(os.path.join(infra_base_path, "base_per_area", '{}_{}.feather'.format(area,ci_system))) #open as geofeather
    #            cisi_exposure_base_area[ci_system] = grid_data_area
    #            cisi_exposure_base_area[ci_system].geometry = pygeos.to_wkb(cisi_exposure_base_area[ci_system].geometry)
    #        else:
    #            cisi_exposure_base_area[ci_system] = pd.DataFrame()

    #    return area,cisi_exposure_base_area
    
    #else: #otherwise, start base calculations

    fetched_data_dict = {group: pd.DataFrame() for group in groups_list} #Create dictionary with asset groups as keys and df as value
    print("Time to import the fetched data files and put it in a dictionairy for base calculations for area: {}".format(area))

    #get fetched_data_dict for area
    for group in groups_list:
        if os.path.isfile(os.path.join(fetched_infra_path, '{}_{}.feather'.format(area, group))) == True:
            fetched_data_dict[group] = from_geofeather(os.path.join(fetched_infra_path, '{}_{}.feather'.format(area,group))) #open as geofeather                
    
    Path(os.path.join(infra_base_path, "base_per_area")).mkdir(parents=True, exist_ok=True) #create pathway
    if cisi.check_dfs_empty(fetched_data_dict) == False: #df's contain data
        shape_countries = from_geofeather(country_shapes_path) #open as geofeather
        country_shape = shape_countries[shape_countries['ISO_3digit'] == area]
        if country_shape.empty == False: #if ISO_3digit in shape_countries
            spat_tree = pygeos.STRtree(grid_data.geometry)
            grid_data_area = (grid_data.loc[spat_tree.query(country_shape.geometry.iloc[0],predicate='intersects').tolist()]).sort_index(ascending=True) #get grids that overlap with cover_box
            grid_data_area = grid_data_area.reset_index().rename(columns = {'index':'grid_number'}) #get index as column and name column grid_number
        else:
            print("Area '{}' not specified in file containing shapefiles of countries with ISO_3digit codes. Grid file will be clipped based on an overlay with infrastructure data".format(area))
            #abstract grid cells that overlap with boundaries of infrastructure data 
            cover_box = gridmaker.create_cover_box(gridmaker.box_per_df(fetched_data_dict)) #create a box based on the boundaries of the assets to be analyzed
            spat_tree = pygeos.STRtree(grid_data.geometry) # https://pygeos.readthedocs.io/en/latest/strtree.html
            grid_data_area = (grid_data.loc[spat_tree.query(cover_box.geometry.iloc[0],predicate='intersects').tolist()]).sort_index(ascending=True) #get grids that overlap with cover_box
            grid_data_area = grid_data_area.reset_index().rename(columns = {'index':'grid_number'}) #get index as column and name column grid_number
        
        #start base calculations
        cisi_exposure_base_area = cisi_exposure.base_calculations(infrastructure_systems, fetched_data_dict, grid_data_area)

        #and save base calculations per area as geofeather
        for ci_system in cisi_exposure_base_area:
            if cisi_exposure_base_area[ci_system].empty == False:
                temp_df = cisi_exposure.transform_to_gpd((cisi_exposure_base_area[ci_system])) #transform df to gpd with shapely geometries
                temp_df.to_file(os.path.join(infra_base_path, "base_per_area", '{}_{}.gpkg'.format(area, ci_system)), layer=' ', driver="GPKG")
                to_geofeather(cisi_exposure_base_area[ci_system], os.path.join(infra_base_path, "base_per_area", '{}_{}.feather'.format(area, ci_system)), crs="EPSG:4326") #save as geofeather
                #with Geopackage(os.path.join(infra_base_path, "base_per_area", '{}_{}.gpkg'.format(area, ci_system)), 'w') as out:
                #    out.add_layer(cisi_exposure_base_area[ci_system], name=' ', crs='EPSG:4326')
                cisi_exposure_base_area[ci_system].geometry = pygeos.to_wkb(cisi_exposure_base_area[ci_system].geometry)
        print("Base calculations are finished and data is exported for area: {}".format(area))

        return area,cisi_exposure_base_area
    else:
        print("WARNING: there is no infrastructure extracted for area '{}'. Please check if OSM-file is correct and matches polygon of area (country_shape)".format(area))
        cisi_exposure_base_area = {ci_system: pd.DataFrame() for ci_system in infrastructure_systems} #create empty dictionary 
        
        return area,cisi_exposure_base_area
    
    #except Exception as e:
    #    print('TEMPORARY EXCEPTION ERROR: {} for {}'.format(e, area))

def base_calculations(local_path):
    """function to calculate the amount of infrastructure per area (e.g. per country) using parallel processing 
    Args:
        *local_path*: Local pathway. Defaults to os.path.join('/scistor','ivm','snn490').
    """

    # get settings
    infrastructure_systems,weight_assets = set_variables()[0:2]

    # run the base calculation parallel per area
    #listed_areas = list(areas.values())[0]
    print('Time to start base calcualations for the following areas: {}'.format(areas))
    with Pool(cpu_count()-1) as pool: 
        cisi_exposure_per_area = dict(pool.starmap(base_calculation_per_area,zip(areas,
                                                        repeat(infrastructure_systems,len(areas)),
                                                        repeat(local_path,len(areas))),
                                                        chunksize=1))
    
    # get paths
    grid_path,infra_base_path = set_paths(local_path,base_calculation=True)[0],set_paths(local_path,base_calculation=True)[2]

    # get grid data
    grid_data = from_geofeather(grid_path) #open as geofeather

    #create cisi_exposure_base for total area
    cisi_exposure_base = {ci_system: grid_data.copy() for ci_system in infrastructure_systems}

    #create lists with assets per ci_system which can be used to make columns in cisi_exposure_base
    asset_dict = {}
    for ci_system in weight_assets:
        asset_dict[ci_system] = []
        for group in weight_assets[ci_system]:
            for asset in weight_assets[ci_system][group]:
                asset_dict[ci_system].append(asset)

    #get all assets as columns and set to 0
    listofzeros = [0.0] * len(grid_data) #get list with zeros
    for ci_system in infrastructure_systems:
        for asset in asset_dict[ci_system]:
            cisi_exposure_base[ci_system].insert(0, asset, listofzeros)
            
    #get fetched_data_dict for area
    print('Time to start summary base calcualations for the following areas: {}'.format(areas))
    for area in areas:        
        for ci_system in infrastructure_systems:
            #if os.path.isfile(os.path.join(infra_base_path, "base_per_area", '{}_{}.feather'.format(area,ci_system))) == True:
            if cisi_exposure_per_area[area][ci_system].empty == False:
                #grid_data_area = from_geofeather(os.path.join(infra_base_path, "base_per_area",'{}_{}.feather'.format(area,ci_system))) #open as geofeather
                grid_data_area = cisi_exposure_per_area[area][ci_system]
                grid_data_area.geometry = pygeos.from_wkb(grid_data_area.geometry)
                #go through df containing basic calculations and put information in one common df
                for asset in asset_dict[ci_system]:
                    if '{}'.format(asset) in grid_data_area.columns:
                        for grid_cell in grid_data_area.itertuples(index=False):
                            if getattr(grid_cell, asset) != 0.0: 
                                cisi_exposure_base[ci_system].loc[getattr(grid_cell, "grid_number"), "{}".format(asset)] += getattr(grid_cell, asset)
            else:
                print("WARNING: the following {}/{} combination does not exist".format(area, ci_system))
                    
    #and save summary base calculations as geofather
    for ci_system in cisi_exposure_base:                                             
        temp_df = cisi_exposure.transform_to_gpd((cisi_exposure_base[ci_system])) #transform df to gpd with shapely geometries
        temp_df.to_file(os.path.join(infra_base_path, 'summary_basecalcs_{}.gpkg'.format(ci_system)), layer=' ', driver="GPKG")
        to_geofeather(cisi_exposure_base[ci_system], os.path.join(infra_base_path, 'summary_basecalcs_{}.feather'.format(ci_system)), crs="EPSG:4326") #save as geofeather
        #with Geopackage(os.path.join(infra_base_path, 'summary_basecalcs_{}.gpkg'.format(ci_system)), 'w') as out:
        #    out.add_layer(cisi_exposure_base[ci_system], name=' ', crs='EPSG:4326')
    print("(Summary) base calculations are finished and data is exported")


def base_calculations_global(local_path):
    """function to calculate the amount of infrastructure per area (e.g. per country) using parallel processing 
    Args:
        *local_path*: Local pathway. Defaults to os.path.join('/scistor','ivm','snn490').
    """

    # get settings
    infrastructure_systems,weight_assets = set_variables()[0:2]
    
    # get paths
    grid_path,infra_base_path = set_paths(local_path,base_calculation=True)[0],set_paths(local_path,base_calculation=True)[2]

    # get grid data
    grid_data = from_geofeather(grid_path) #open as geofeather

    #create cisi_exposure_base for total area
    cisi_exposure_base = {ci_system: grid_data.copy() for ci_system in infrastructure_systems}

    #create lists with assets per ci_system which can be used to make columns in cisi_exposure_base
    asset_dict = {}
    for ci_system in weight_assets:
        asset_dict[ci_system] = []
        for group in weight_assets[ci_system]:
            for asset in weight_assets[ci_system][group]:
                asset_dict[ci_system].append(asset)

    #get all assets as columns and set to 0
    listofzeros = [0.0] * len(grid_data) #get list with zeros
    for ci_system in infrastructure_systems:
        for asset in asset_dict[ci_system]:
            cisi_exposure_base[ci_system].insert(0, asset, listofzeros)
            
    #get fetched_data_dict for area
    print('Time to start summary base calcualations for the following areas: {}'.format(areas))
    for ci_system in infrastructure_systems:
        for area in areas:        
            if os.path.isfile(os.path.join(infra_base_path, "base_per_area", '{}_{}.feather'.format(area,ci_system))) == True:
                grid_data_area = from_geofeather(os.path.join(infra_base_path, "base_per_area",'{}_{}.feather'.format(area,ci_system))) #open as geofeather
                if grid_data_area.empty == False:
                    #grid_data_area.geometry = pygeos.from_wkb(grid_data_area.geometry)
                    #go through df containing basic calculations and put information in one common df
                    for asset in asset_dict[ci_system]:
                        if '{}'.format(asset) in grid_data_area.columns:
                            for grid_cell in grid_data_area.itertuples(index=False):
                                if getattr(grid_cell, asset) != 0.0: 
                                    cisi_exposure_base[ci_system].loc[getattr(grid_cell, "grid_number"), "{}".format(asset)] += getattr(grid_cell, asset)
                else:
                    print("WARNING: the {}_{} file for base calculations is empty".format(area, ci_system))
            else:
                print("WARNING: the {}_{} file for base calculations does not exist".format(area, ci_system))
        
        #calculations for each area for a specific ci_system are done. Time to export summary data for ci_system       
        print('Summary base calculations are done for {}. Will be exported now...'.format(ci_system))#and save summary base calculations as geofather                                            
        temp_df = cisi_exposure.transform_to_gpd((cisi_exposure_base[ci_system])) #transform df to gpd with shapely geometries
        temp_df.to_file(os.path.join(infra_base_path, 'summary_basecalcs_{}.gpkg'.format(ci_system)), layer=' ', driver="GPKG")
        to_geofeather(cisi_exposure_base[ci_system], os.path.join(infra_base_path, 'summary_basecalcs_{}.feather'.format(ci_system)), crs="EPSG:4326") #save as geofeather
        #with Geopackage(os.path.join(infra_base_path, 'summary_basecalcs_{}.gpkg'.format(ci_system)), 'w') as out:
        #    out.add_layer(cisi_exposure_base[ci_system], name=' ', crs='EPSG:4326')
        print("(Summary) base calculations are finished and data is exported")

################################################################
            ## Step 3: Perform cisi calculations ##
################################################################

def cisi_calculation(local_path,goal_area):
    """function to calculate the index per area (e.g. per country) using parallel processing 

    Args:
        *local_path*: Local pathway. Defaults to os.path.join('/scistor','ivm','snn490').
    """ 

    # get settings
    infrastructure_systems,weight_assets,weight_groups,weight_subsystems = set_variables() 

    # get paths
    method_max_path,method_mean_path,infra_base_path = set_paths(local_path,cisi_calculation=True)    

    # get cisi_exposure_base data
    if 'cisi_exposure_base' in globals() or 'cisi_exposure_base' in locals():
        print("cisi_exposure_base dictionary is ready for CISI analysis")
    else:
        print("Time to import the infrastructure datafiles containing the summary base calculations and put it in a dictionairy for CISI analysis")
        cisi_exposure_base = {ci_system: pd.DataFrame() for ci_system in infrastructure_systems} #use keys in infrastructure_systems to make dataframes for indices https://stackoverflow.com/questions/56217737/use-elements-in-a-list-for-dataframe-names
        #import infrastructure data of each subsystem and save in dictionary
        for ci_system in infrastructure_systems:
            if os.path.isfile(os.path.join(infra_base_path, 'summary_basecalcs_{}.feather'.format(ci_system))) == True:
                infra_base_data = from_geofeather(os.path.join(infra_base_path, 'summary_basecalcs_{}.feather'.format(ci_system))) #open as geofeather
                cisi_exposure_base[ci_system] = infra_base_data #save data in dictionary
            else:
                print("WARNING: the following file summary_basecalcs_{}.feather does not exist".format(ci_system))

    ## method 1 ##
    output_overall_max = cisi_exposure.cisi_overall_max_single(weight_assets, weight_groups, weight_subsystems, infrastructure_systems, cisi_exposure_base)

    #Create folders for outputs (GPKGs and pngs)
    Path(method_max_path).mkdir(parents=True, exist_ok=True)
    #export as gpkg and geofeather
    to_geofeather((output_overall_max[0]), os.path.join(method_max_path,'CISI_exposure_{}.feather'.format(goal_area)), crs="EPSG:4326") #save as geofeather
    #temp_df = cisi_exposure.transform_to_gpd((output_overall_max[0])) #transform df to gpd with shapely geometries
    #temp_df.to_file(os.path.join(method_max_path,'CISI-exposure.gpkg'), layer='method max', driver="GPKG")

    #make plots of final exposure index, and sub indices, and save automatically 
    cisi_exposure.make_plots_automatic(output_overall_max[1], output_overall_max[0], goal_area, method_max_path)


    ## method 1 without normalization ##
    output_overall_max1 = cisi_exposure.cisi_overall_max_single_no_normalization(weight_assets, weight_groups, weight_subsystems, infrastructure_systems, cisi_exposure_base)

    #Create folders for outputs (GPKGs and pngs)
    method_max_path_extended = os.path.join(method_max_path, 'non_normalized')
    Path(method_max_path_extended).mkdir(parents=True, exist_ok=True)
    #export as gpkg and geofeather
    to_geofeather((output_overall_max1[0]), os.path.join(method_max_path_extended,'CISI_exposure_{}.feather'.format(goal_area)), crs="EPSG:4326") #save as geofeather
    #temp_df = cisi_exposure.transform_to_gpd((output_overall_max1[0])) #transform df to gpd with shapely geometries
    #temp_df.to_file(os.path.join(method_max_path_extended,'CISI-exposure.gpkg'), layer='method max', driver="GPKG")

    #make plots of final exposure index, and sub indices, and save automatically 
    cisi_exposure.make_plots_automatic(output_overall_max1[1], output_overall_max1[0], goal_area, method_max_path_extended)


    ## method 2 ##
    #output_overall_mean = cisi_exposure.cisi_overall_mean_single(weight_assets, weight_groups, weight_subsystems,infrastructure_systems, cisi_exposure_base)

    #Create folders for outputs (GPKGs and pngs)
    #method_mean_path_extended = os.path.join(method_mean_path, 'overall_mean')
    #Path(method_mean_path).mkdir(parents=True, exist_ok=True)
    #export as gpkg
    #to_geofeather((output_overall_mean[0]), os.path.join(method_mean_path,'CISI_exposure_{}.feather'.format(goal_area)), crs="EPSG:4326") #save as geofeather
    #temp_df = cisi_exposure.transform_to_gpd((output_overall_mean[0])) #transform df to gpd with shapely geometries
    #temp_df.to_file(os.path.join(method_mean_path,'CISI-exposure_{}.gpkg'.format(goal_area)), layer='method mean', driver="GPKG")

    #make plots of final exposure index, and sub indices, and save automatically 
    #cisi_exposure.make_plots_automatic(output_overall_mean[1], output_overall_mean[0], goal_area, method_mean_path)
    
if __name__ == '__main__':
    #receive nothing, run area below
    if (len(sys.argv) == 1):    
        areas = ['Galveston_Bay']#['Zuid-Holland']
        run_all(areas)
    else:
        # receive ISO code, run one country
        if (len(sys.argv) > 1) & (len(sys.argv[1]) == 3):    
            areas = []
            areas.append(sys.argv[1])
            run_all(areas)
        #receive multiple ISO-codes in a list, run specified countries
        elif '[' in sys.argv[1]:
            if ']' in sys.argv[1]:
                areas = sys.argv[1].strip('][').split('.') 
                run_all(areas)
            else:
                print('FAILED: Please write list without space between list-items. Example: [NLD.LUX.BEL]')
        #receive global, run all countries in the world
        elif (len(sys.argv) > 1) & (sys.argv[1] == 'global'):    
            #glob_info = pd.read_excel(os.path.join('/scistor','ivm','snn490','Datasets','global_information_short.xlsx'))
            #glob_info = pd.read_excel(os.path.join(r'C:\Users\snn490\surfdrive\Datasets','global_information_test.xlsx'))
            glob_info = pd.read_excel(os.path.join('/scistor','ivm','snn490','Datasets','global_information_advanced.xlsx'))
            areas = list(glob_info.ISO_3digit) 
            if len(areas) == 0:
                print('FAILED: Please check file with global information')
            else:
                run_all(areas)
        #receive continent, run all countries in continent
        elif (len(sys.argv) > 1) & (len(sys.argv[1]) > 3):    
            #glob_info = pd.read_excel(os.path.join('/scistor','ivm','snn490','Datasets','global_information_short.xlsx'))
            #glob_info = pd.read_excel(os.path.join(r'C:\Users\snn490\surfdrive\Datasets','global_information_test.xlsx'))
            glob_info = pd.read_excel(os.path.join('/scistor','ivm','snn490','Datasets','global_information_advanced.xlsx'))
            glob_info = glob_info.loc[glob_info.continent==sys.argv[1]]
            areas = list(glob_info.ISO_3digit) 
            if len(areas) == 0:
                print('FAILED: Please write the continents as follows: Africa, Asia, Central-America, Europe, North-America,Oceania, South-America') 
            else:
                run_all(areas)
        else:
            print('FAILED: Either provide an ISO3 country name or a continent name')