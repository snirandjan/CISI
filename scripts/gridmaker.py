"""
Make gridcells based on outercorners of the shape of the inputfile and specified resolution (e.g. 0.1 degrees). 
Inputs: 
- df = inputfile containing shape 
- height = resolution in degrees
  
@Author: Elco Koks & Sadhana Nirandjan - Institute for Environmental studies, VU University Amsterdam
"""

import pygeos
import numpy as np
import pandas as pd

def create_grid(df, height, buffer):
    """Create grids  
    Arguments:
        *df*: geodataframe with spatial data 
        *height*: desired resolution in degrees (e.g. 0.1)
        *buffer*: buffer in degrees (e.g. 0)
        
    Returns:
        Geodataframe containing consistent grids that overlap with *df*
    """
    
    bbox = pygeos.buffer(pygeos.creation.box(pygeos.total_bounds(df.geometry)[0],
                                  pygeos.total_bounds(df.geometry)[1],
                                  pygeos.total_bounds(df.geometry)[2],
                                  pygeos.total_bounds(df.geometry)[3]),buffer)

    xmin, ymin = pygeos.total_bounds(bbox)[0],pygeos.total_bounds(bbox)[1]
    xmax, ymax = pygeos.total_bounds(bbox)[2],pygeos.total_bounds(bbox)[3]
    rows = int(np.ceil((ymax-ymin) / height))
    cols = int(np.ceil((xmax-xmin) / height))
    x_left_origin = xmin
    x_right_origin = xmin + height
    y_top_origin = ymax
    y_bottom_origin = ymax - height
    res_geoms = []
    for countcols in range(cols):
        y_top = y_top_origin
        y_bottom = y_bottom_origin
        for countrows in range(rows):
            res_geoms.append(pygeos.polygons(
                ((x_left_origin, y_top), (x_right_origin, y_top),
                (x_right_origin, y_bottom), (x_left_origin, y_bottom)
                )))
            y_top = y_top - height
            y_bottom = y_bottom - height
        x_left_origin = x_left_origin + height
        x_right_origin = x_right_origin + height
    return res_geoms

def create_cover_box(df):
    """get df with boundary coordinates
    Arguments:
        *fetched_data_dict* : dictionary with df containing geospatial data as values 
        
    Returns:
        df with single boundary polygon 
    """
    bbox = pygeos.buffer(pygeos.creation.box(pygeos.total_bounds(df.geometry)[0],
                                  pygeos.total_bounds(df.geometry)[1],
                                  pygeos.total_bounds(df.geometry)[2],
                                  pygeos.total_bounds(df.geometry)[3]),0)

    xmin, ymin = pygeos.total_bounds(bbox)[0],pygeos.total_bounds(bbox)[1]
    xmax, ymax = pygeos.total_bounds(bbox)[2],pygeos.total_bounds(bbox)[3]

    res_geoms = []
    res_geoms.append(pygeos.polygons(
        ((xmin, ymax), (xmax, ymax),
        (xmax, ymin), (xmin, ymin)
        )))

    cover_box = pd.DataFrame(res_geoms,columns=['geometry'])

    return cover_box

def box_per_df(fetched_data_dict):
    """get df with boundary coordinates of each df
    Arguments:
        *fetched_data_dict* : dictionary with df containing geospatial data as values 
        
    Returns:
        df with polygons (number of polygons depends on number of df with geospatial data)
    """
    res_geoms = []
    for group in fetched_data_dict:
        if fetched_data_dict[group].empty == False:
            if len(fetched_data_dict[group].index) > 1:
                bbox = pygeos.buffer(pygeos.creation.box(pygeos.total_bounds(fetched_data_dict[group].geometry)[0],
                                            pygeos.total_bounds(fetched_data_dict[group].geometry)[1],
                                            pygeos.total_bounds(fetched_data_dict[group].geometry)[2],
                                            pygeos.total_bounds(fetched_data_dict[group].geometry)[3]),0)
                xmin, ymin = pygeos.total_bounds(bbox)[0],pygeos.total_bounds(bbox)[1]
                xmax, ymax = pygeos.total_bounds(bbox)[2],pygeos.total_bounds(bbox)[3]
                res_geoms.append(pygeos.polygons(
                    ((xmin, ymax), (xmax, ymax),
                    (xmax, ymin), (xmin, ymin)
                    )))
            elif len(fetched_data_dict[group].index) == 1 and pygeos.geometry.get_type_id(fetched_data_dict[group].iloc[0]["geometry"]) != 0: #one asset, but not point data
                bbox = pygeos.buffer(pygeos.creation.box(pygeos.total_bounds(fetched_data_dict[group].geometry)[0],
                                            pygeos.total_bounds(fetched_data_dict[group].geometry)[1],
                                            pygeos.total_bounds(fetched_data_dict[group].geometry)[2],
                                            pygeos.total_bounds(fetched_data_dict[group].geometry)[3]),0)
                xmin, ymin = pygeos.total_bounds(bbox)[0],pygeos.total_bounds(bbox)[1]
                xmax, ymax = pygeos.total_bounds(bbox)[2],pygeos.total_bounds(bbox)[3]
                res_geoms.append(pygeos.polygons(
                    ((xmin, ymax), (xmax, ymax),
                    (xmax, ymin), (xmin, ymin)
                    )))                

    bbox_df = pd.DataFrame(res_geoms,columns=['geometry'])
    return bbox_df