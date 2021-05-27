################################################################
                ## Load package and set path ##
################################################################
import os,sys
import pygeos
import math
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.gridspec as gridspec
from pathlib import Path
from pgpkg import Geopackage
from shapely.wkb import loads
from geopandas import GeoDataFrame
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm
#pip install geofeather
from geofeather.pygeos import to_geofeather, from_geofeather
from matplotlib import scale as mscale
from matplotlib.ticker import MultipleLocator

sys.path.append("C:\Projects\Coastal_Infrastructure\scripts")
import cisi
import cisi_exposure
import extract
import gridmaker

normalized_dataset = ['normalized']
for n_data in normalized_dataset:
    # Set your local pathway
    #cisi_normalized
    base_path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Outputs','Exposure','CISI_global'))
    method_max_path = os.path.abspath(os.path.join(base_path, 'index_010', 'method_max')) #save figures
    
    if n_data == 'normalized':
        #import data
        #df = from_geofeather(os.path.join(method_max_path, 'CISI-exposure.feather')) #open as geofeather
        gdf_global = gpd.read_file(os.path.join(method_max_path, 'CISI_exposure_Global.gpkg')) #open as geofeather
        #gdf_global = from_geofeather(os.path.join(method_max_path, 'CISI_exposure_Global.feather')) #open as geofeather
    elif n_data == 'non_normalized':
        #import data
        #df = from_geofeather(os.path.join(method_max_path, 'CISI-exposure.feather')) #open as geofeather
        gdf_global = gpd.read_file(os.path.join(method_max_path, 'non_normalized','CISI_exposure_Global.gpkg')) #open as geofeather
        #gdf_global = from_geofeather(os.path.join(method_max_path, 'CISI_exposure_Global.feather')) #open as geofeather

    #transform to geopandas
    #df['geometry']=df.geometry.apply(lambda x : loads(pygeos.to_wkb(x))) 
    #gdf = GeoDataFrame(df,  crs="EPSG:4326", geometry='geometry')

    #world boundaries
    #world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')
    shapes_file = 'global_countries_advanced.geofeather'
    country_shapes_path = os.path.abspath(os.path.join('/scistor','ivm','snn490','Datasets','Administrative_boundaries', 'global_countries_buffer', shapes_file)) #shapefiles with buffer around country
    shape_countries = from_geofeather(country_shapes_path)

    #transform to geopandas
    shape_countries['geometry']=shape_countries.geometry.apply(lambda x : loads(pygeos.to_wkb(x))) 
    shape_countries = GeoDataFrame(shape_countries,  crs="EPSG:4326", geometry='geometry')

    letters =['A','B','C','D']
    color_ramp = ['gist_heat_r']

    for ramp in color_ramp:
        fig6 = plt.figure(constrained_layout=False, figsize=(15, 10))
        gs = fig6.add_gridspec(2, 3, height_ratios=[3,2], width_ratios=[1, 1, 1], wspace=0.03, hspace=0.0)#)
        #gs = fig3.add_gridspec(nrows=3, ncols=3, left=0.05, right=0.48, wspace=0.05)
        f6_ax1 = fig6.add_subplot(gs[0, 0:3])
        #f3_ax1.set_title('gs[0, :]')
        f6_ax1.text(0.0145, 0.98, '{}'.format(letters[0]), transform=f6_ax1.transAxes,
                fontweight="bold",color='black', fontsize=15, verticalalignment='top',horizontalalignment='center',
                bbox= dict(boxstyle='square', facecolor='white', alpha=0.5,linewidth=0))


        f6_ax2 = fig6.add_subplot(gs[1, :-2])
        #f3_ax2.set_title('gs[1, :-1]')
        f6_ax2.text(0.05, 1.09, '{}'.format(letters[1]), transform=f6_ax2.transAxes,
                    fontweight="bold",color='black', fontsize=15, verticalalignment='top',horizontalalignment='center',
                    bbox= dict(boxstyle='square', facecolor='white', alpha=0,linewidth=0))
        f6_ax2.text(0.5, 1.065, '{}'.format('East Coast of the US'), transform=f6_ax2.transAxes,
                    fontweight="bold",color='black', fontsize=10, verticalalignment='top',horizontalalignment='center',
                    bbox= dict(boxstyle='square', facecolor='white', alpha=0.5,linewidth=0))

        f6_ax3 = fig6.add_subplot(gs[1:, -2])
        #f3_ax3.set_title('gs[1:, -1]')
        f6_ax3.text(0.05, 1.09, '{}'.format(letters[2]), transform=f6_ax3.transAxes,
                    fontweight="bold",color='black', fontsize=15, verticalalignment='top',horizontalalignment='center',
                    bbox= dict(boxstyle='square', facecolor='white', alpha=0,linewidth=0))
        f6_ax3.text(0.5, 1.065, '{}'.format('Western Europe'), transform=f6_ax3.transAxes,
                    fontweight="bold",color='black', fontsize=10, verticalalignment='top',horizontalalignment='center',
                    bbox= dict(boxstyle='square', facecolor='white', alpha=0.5,linewidth=0))

        f6_ax4 = fig6.add_subplot(gs[1:, -1])
        f6_ax4.text(0.05, 1.09, '{}'.format(letters[3]), transform=f6_ax4.transAxes,
                    fontweight="bold",color='black', fontsize=15, verticalalignment='top',horizontalalignment='center',
                    bbox= dict(boxstyle='square', facecolor='white', alpha=0,linewidth=0))
        f6_ax4.text(0.5, 1.065, '{}'.format('East Asia'), transform=f6_ax4.transAxes,
                    fontweight="bold",color='black', fontsize=10, verticalalignment='top',horizontalalignment='center',
                    bbox= dict(boxstyle='square', facecolor='white', alpha=0.5,linewidth=0))

        #get limits of grids (https://www.earthdatascience.org/courses/scientists-guide-to-plotting-data-in-python/plot-spatial-data/customize-vector-plots/python-change-spatial-extent-of-map-matplotlib-geopandas/)
        #xlim = ([gdf_global["geometry"].total_bounds[0],  gdf_global["geometry"].total_bounds[2]])
        #ylim = ([gdf_global["geometry"].total_bounds[1],  gdf_global["geometry"].total_bounds[3]])

        # plot
        #f6_ax1.set_xlim(xlim)
        #f6_ax1.set_ylim(ylim)

        #to allign color bar with figure
        divider = make_axes_locatable(f6_ax1)
        cax = divider.append_axes("right", size="3%", pad=0)

        #world.boundary.plot(edgecolor="black", linewidth=0.50, ax=f6_ax1)
        shape_countries.plot(edgecolor="black", facecolor='lightgrey', linewidth=0.25, ax=f6_ax1) #plot background

        gdf_global.plot(column='CISI_exposure',
                cmap=ramp,
                legend=True,
                norm = TwoSlopeNorm(vmin=0, vcenter=0.25, vmax=1),
                ax=f6_ax1, 
                vmax=1,
                cax=cax) #vmax=gdf_global['transportation_unique_count'].max()
                #missing_kwds={'color': 'lightgrey'}
                
        shape_countries.plot(edgecolor="black", facecolor='None', linewidth=0.15, ax=f6_ax1)   #plot border            
        cax.set_ylabel('CISI', rotation=0, fontsize=11) #fontdict=dict(weight='bold'))
        cax.yaxis.set_label_coords(0.5,1.032)
        f6_ax1.set_axis_off()
        print('Plot {} done'.format(letters[0]))

        #figure 5b: USA
        #get limits of grids (https://www.earthdatascience.org/courses/scientists-guide-to-plotting-data-in-python/plot-spatial-data/customize-vector-plots/python-change-spatial-extent-of-map-matplotlib-geopandas/)
        xlim = ([-97, -66])
        ylim = ([24, 47.9])

        # plot
        f6_ax2.set_xlim(xlim)
        f6_ax2.set_ylim(ylim)

        shape_countries.plot(edgecolor="black", facecolor='lightgrey', linewidth=0.25, ax=f6_ax2) #plot background

        gdf_global.plot(column='CISI_exposure',
                cmap=ramp, 
                legend=False,
                ax=f6_ax2, 
                vmax=1) 
                #linewidth=0.01, edgecolor="#04253a") #vmax=gdf_global['transportation_unique_count'].max()
                #missing_kwds={'color': 'lightgrey'}

        shape_countries.plot(edgecolor="black", facecolor='None', linewidth=0.15, ax=f6_ax2)   #plot border
                        

        #f6_ax2.set_axis_off()
        f6_ax2.set_yticklabels([])
        f6_ax2.set_xticklabels([])
        f6_ax2.set_yticks([])
        f6_ax2.set_xticks([])
        print('Plot {} done'.format(letters[1]))


        #figure 5c: Europe
        #get limits of grids (https://www.earthdatascience.org/courses/scientists-guide-to-plotting-data-in-python/plot-spatial-data/customize-vector-plots/python-change-spatial-extent-of-map-matplotlib-geopandas/)
        xlim = ([-11,17.5])
        ylim = ([41,63])

        # plot
        f6_ax3.set_xlim(xlim)
        f6_ax3.set_ylim(ylim)

        shape_countries.plot(edgecolor="black", facecolor='lightgrey', linewidth=0.25, ax=f6_ax3) #plot background

        gdf_global.plot(column='CISI_exposure',
                cmap=ramp,
                legend=False,
                ax=f6_ax3, 
                vmax=1) 
                #linewidth=0.01, edgecolor="#04253a") #vmax=gdf_global['transportation_unique_count'].max()
                #missing_kwds={'color': 'lightgrey'}

        shape_countries.plot(edgecolor="black", facecolor='None', linewidth=0.15, ax=f6_ax3)   #plot border
                        

        #f6_ax2.set_axis_off()
        f6_ax3.set_yticklabels([])
        f6_ax3.set_xticklabels([])
        f6_ax3.set_yticks([])
        f6_ax3.set_xticks([])
        print('Plot {} done'.format(letters[2]))

        #figure 5d: East Asia
        #get limits of grids (https://www.earthdatascience.org/courses/scientists-guide-to-plotting-data-in-python/plot-spatial-data/customize-vector-plots/python-change-spatial-extent-of-map-matplotlib-geopandas/)
        xlim = ([70,148])
        ylim = ([10,70])

        # plot
        f6_ax4.set_xlim(xlim)
        f6_ax4.set_ylim(ylim)

        shape_countries.plot(edgecolor="black", facecolor='lightgrey', linewidth=0.25, ax=f6_ax4) #plot background

        gdf_global.plot(column='CISI_exposure',
                cmap=ramp, 
                legend=False,
                ax=f6_ax4, 
                vmax=1) 
                #linewidth=0.01, edgecolor="#04253a") #vmax=gdf_global['transportation_unique_count'].max()
                #missing_kwds={'color': 'lightgrey'}

        shape_countries.plot(edgecolor="black", facecolor='None', linewidth=0.15, ax=f6_ax4)   #plot border
                        
        #f6_ax2.set_axis_off()
        f6_ax4.set_yticklabels([])
        f6_ax4.set_xticklabels([])
        f6_ax4.set_yticks([])
        f6_ax4.set_xticks([])
        print('Plot {} done'.format(letters[3]))


        #save figure
        #Create folders for outputs (GPKGs and pngs)
        output_path = os.path.join(base_path, 'figure_6', n_data)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        fig6.savefig(os.path.join(output_path, 'Fig6_{}_{}_ratio32_v8.png'.format(ramp, n_data)), bbox_inches='tight', dpi=1000)