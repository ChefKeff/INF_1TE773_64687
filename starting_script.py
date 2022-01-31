##################################################################################
# 
# Solar irradiance data from STRÃ…NG: 
#   https://strang.smhi.se/extraction/index.php
# 
# Modeled wind power data from Varberg's wind power plant Munkagård
#   latitude: 57.033110, longitude: 12.382547
#   Information: https://www.varbergenergi.se/om-oss/var-verksamhet/vind/
#   Map: https://goo.gl/maps/e1nNWy4JR1QN27N49
#
# Electricity price data from NordPool: 
#   https://www.nordpoolgroup.com/historical-market-data/
#
##################################################################################


import os
import pandas as pd
import numpy as np
from pvlib import location, irradiance, pvsystem

PATH ='C:/Users/oskli230/Box/Optimal sizing' # Path where your files are stored
os.chdir(PATH)
df_data = pd.read_csv('model_data.csv')

# Define location parameters
lat, lon = 57.033110, 12.382547 # Coordinates to Varberg
tz = 'UTC'
site = location.Location(lat,lon,tz=tz)

# Pre-process data
df_dates = pd.date_range(start = str(df_data["Year"][0]) + "-" + str(df_data["Month"][0]) + "-" + str(df_data["Day"][0]) + " " + str(df_data["HourOfDay"][0]) + ":00:00", 
                         end = str(df_data["Year"].iloc[-1]) + "-" + str(df_data["Month"].iloc[-1]) + "-" + str(df_data["Day"].iloc[-1]) + " " + str(df_data["HourOfDay"].iloc[-1]) + ":00:00",
                         freq = "1H",
                         tz=site.tz)

df_wp = pd.DataFrame({'wp': df_data["Windfarm1"]}).set_index(pd.to_datetime(df_dates.values, utc = True))
df_irr = pd.DataFrame({'dhi': df_data["DHI"], 'dni': df_data["DNI"], 'ghi': df_data["GHI"]}).set_index(pd.to_datetime(df_dates.values, utc = True))
df_spot_price = pd.DataFrame({'spot': df_data["Price [SEK/MWh]"]/1000}).set_index(pd.to_datetime(df_dates.values, utc = True)) # SEK/kWh

# Create function for re-use at different tilts/azimuths
def get_poa(site_location, date, irr, tilt, surface_azimuth):
    #clearsky = site_location.get_clearsky(date) # Get the clear sky irradiance
    solar_position = site_location.get_solarposition(times=date)
    POA_irradiance = irradiance.get_total_irradiance(surface_tilt=tilt,
                                                     surface_azimuth=surface_azimuth,
                                                     dni=irr["dni"],
                                                     ghi=irr["ghi"],
                                                     dhi=irr["dhi"],
                                                     solar_zenith=solar_position['apparent_zenith'],
                                                     solar_azimuth=solar_position['azimuth'],
                                                     albedo=0.2)
    return pd.DataFrame({'POA': POA_irradiance['poa_global']})

# Define module and inverter properties
module_parameters = {'pdc0': 100, 'gamma_pdc': -0.004}
inverter_parameters = {'pdc0': 100, 'eta_inv_nom': 0.96}
system = pvsystem.PVSystem(module_parameters=module_parameters,
                           inverter_parameters=inverter_parameters)

# Define system properties
solar_zenith = 0
panel_tilt = np.linspace(0, 180, 100)      # To be optimized
azimuth = np.linspace(0, 360, 100)         # To be optimized

trafo_limit = max(df_wp['wp'])             # Define transformer limit
max_curtail = 5                            # Maximum allowed curtailment in percent [%]

# From here on you need to model the park! 
