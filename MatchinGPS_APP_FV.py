# pipenv shell
# Ruta de prueba origen: Calle Colon 10,  Valencia -- destino: Avenida Antonio Ferrandis 16
# Estadio del Levante -- Hospital la Fe
import streamlit as st
from streamlit_folium import st_folium, folium_static
import googlemaps
from geopy.geocoders import GoogleV3
import math
import pandas as pd
import pydeck as pdk
import numpy as np
from branca.colormap import LinearColormap
import folium
from folium import plugins
import ipywidgets
from shapely.geometry import Polygon, Point
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import requests
import polyline

st.set_page_config(page_title='GPS APP', page_icon=":tada:", layout='wide')

st.title('MatchinGPS 📍🗺️', anchor='title')

# Path coordinates functions
key_api = "AIzaSyAjEUQX4-Eu5zHl1pHQXlz6PvivM9AxGhA"

def get_distance_time(start, end, key):
    geolocator = GoogleV3(api_key=key)
    gmaps = googlemaps.Client(key=key)

    # Start end points
    start_coor = geolocator.geocode(start)
    end_coor = geolocator.geocode(end)

    # Route part
    directions_result = gmaps.directions((start_coor.latitude, start_coor.longitude), (end_coor.latitude, end_coor.longitude), mode="driving")
    duration = directions_result[0]['legs'][0]['duration']['value']/60
    distance = directions_result[0]['legs'][0]['distance']['value']
    meters, kms = math.modf(distance/1000)
    coordinates = polyline.decode(directions_result[0]['overview_polyline']['points'])
    return duration, kms, meters, coordinates

def get_pick_up(latitude_0, longitude_0, latitude_1, longitude_1, mode_route, key):
    gmaps = googlemaps.Client(key=key)
    directions_result = gmaps.directions((latitude_0, longitude_0), (latitude_1, longitude_1), mode=mode_route)

    # Path coordinates
    coordinates = polyline.decode(directions_result[0]['overview_polyline']['points'])

    # Duration
    duration = directions_result[0]['legs'][0]['duration']['value']/60

    # Distance total
    distance = directions_result[0]['legs'][0]['distance']['value']/1000
    return distance, int(duration), coordinates

col1, col2 = st.columns(2)

try:
    start = st.text_input('**Origen** 🏠')
    end = st.text_input('**Destino** 🚩')
    mins, km, m, route = get_distance_time(start, end, key_api)

    with col1:
        st.write('_Distancia_: ', int(km), 'Kms', int(m*1000), 'metros')
    with col2:
        st.write('_Tiempo estimado_: ', int(np.round(mins)), 'mins')

except:
    st.write('👆Introduce origen y destino 👆')

matrix_1k = np.load("/Users/diegoarcosdelasheras/Desktop/DATA SCIENCE/PROJECT/Google_matrix_1k.npy", allow_pickle=True)
data_set = pd.DataFrame(matrix_1k, columns = ['Coordinates'])

tab1, tab2 = st.tabs(["_Matching entre rutas_ 🤝", "_Tráfico en tiempo real_ 🚗"])

# =================================================================
# Euclidean distance algorithm
# =================================================================

try:
    distances = []
    results = pd.DataFrame()

    with st.spinner('Encontrando las mejores rutas...⌛'):
        for i in range(0,400):
            distance_o_i, path = fastdtw(np.array(route),np.array(data_set.iloc[i]['Coordinates']), dist=euclidean)
            distances.append(distance_o_i)
        results['distance'] = distances
        data_merged = pd.concat([results,data_set], axis=1).sort_values(by='distance').reset_index().drop('index', axis=1)

    similar_points_1 = []
    similar_points_2 = []

    # Puntos ruta y primera mejor ruta
    for i in route:
        for j in data_merged['Coordinates'][0]:
            if i==j:
                similar_points_1.append(i)

    # Puntos ruta y segunda mejor ruta
    for n in route:
        for m in data_merged['Coordinates'][1]:
            if n==m:
                similar_points_2.append(n)

    dist_1, minutes_1, walk_route_1 = get_pick_up(route[0][0], route[0][1], similar_points_1[0][0], similar_points_1[0][1], "walking", key_api)
    dist_2, minutes_2, walk_route_2 = get_pick_up(route[0][0], route[0][1], similar_points_2[0][0], similar_points_2[0][1], "walking", key_api)

# =============================================================================
# Map 1 creation
# =============================================================================

    with tab1:

        map_types = ['1️⃣🏆- Ruta', '2️⃣🏆- Ruta']
        selected_map = st.radio("Selecciona ruta:", options=map_types)

        if selected_map == '1️⃣🏆- Ruta':
            m1 = folium.Map(location=[39.4697500,  -0.3773900], zoom_start=13, title="Stamen Terrain")

            # Add plugins
            plugins.MiniMap(toggle_display = True, position="bottomright").add_to(m1)
            #plugins.MousePosition(position='bottomright').add_to(m1)
            plugins.MeasureControl(position='bottomright').add_to(m1)
            plugins.LocateControl().add_to(m1)
            #plugins.Geocoder(position='topleft', add_marker=True).add_to(m1)
            plugins.Draw().add_to(m1)
            plugins.Fullscreen(position = 'topright').add_to(m1)

            # Add tiles to map
            folium.raster_layers.TileLayer('Stamen Terrain').add_to(m1)
            folium.raster_layers.TileLayer('Open Street Map').add_to(m1)
            folium.raster_layers.TileLayer('Stamen Toner').add_to(m1)
            folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m1)
            folium.raster_layers.TileLayer('CartoDB Positron').add_to(m1)
            folium.raster_layers.TileLayer('CartoDB Dark_Matter').add_to(m1)

            # Pick up point
            folium.Marker(similar_points_1[0], tooltip = 'PICK UP POINT 📌🚗', icon = folium.Icon(color='purple')).add_to(m1)

            # My route
            plugins.AntPath(route, weight=10, opacity=0.7, color = 'blue', tooltip = 'MI RUTA 🛣️').add_to(m1)
            plugins.AntPath(walk_route_1, weight=4, opacity=0.8, color = 'purple', tooltip = 'RUTA A PIE 🚶‍').add_to(m1)
            folium.Marker(route[0], tooltip = 'Inicio Ruta 🏠', icon = folium.Icon(color='blue', icon='home')).add_to(m1)
            folium.Marker(route[-1], tooltip = 'Final Ruta 🚩', icon = folium.Icon(color='blue', icon='flag')).add_to(m1)

            # Best matching
            folium.PolyLine(data_merged['Coordinates'][0], weight=5, opacity=0.9, color = 'green', tooltip = 'MATCH 🎉').add_to(m1)
            folium.Marker(data_merged['Coordinates'][0][0], tooltip = 'Inicio Ruta 🏠', icon = folium.Icon(color='green', icon ='home')).add_to(m1)
            folium.Marker(data_merged['Coordinates'][0][-1], tooltip = 'Final Ruta 🚩', icon = folium.Icon(color='green', icon ='flag')).add_to(m1)

            # Add layer control to show different maps
            folium.LayerControl().add_to(m1)
            folium_static(m1, width=1120)
            st.write('_Distancia a pie_ 🚶‍: ', np.round((dist_1),2), 'Kms')
            st.write('_Tiempo a punto de recogida_: ', int(np.round(minutes_1)), 'mins')

        else:

            m2 = folium.Map(location=[39.4697500,  -0.3773900], zoom_start=13, title="Stamen Terrain")

            # Plugins
            plugins.MiniMap(toggle_display = True, position="bottomleft").add_to(m2)
            #plugins.MousePosition(position='bottomright').add_to(m2)
            plugins.MeasureControl(position='bottomright').add_to(m2)
            plugins.LocateControl().add_to(m2)
            #plugins.Geocoder(position='topleft', add_marker=True).add_to(m2)
            plugins.Draw().add_to(m2)
            plugins.Fullscreen(position = 'topright').add_to(m2)

            # Add tiles to map
            folium.raster_layers.TileLayer('Stamen Terrain').add_to(m2)
            folium.raster_layers.TileLayer('Open Street Map').add_to(m2)
            folium.raster_layers.TileLayer('Stamen Toner').add_to(m2)
            folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m2)
            folium.raster_layers.TileLayer('CartoDB Positron').add_to(m2)
            folium.raster_layers.TileLayer('CartoDB Dark_Matter').add_to(m2)

            # Pick up point
            folium.Marker(similar_points_2[0], tooltip = 'PICK UP POINT 📌🚗', icon = folium.Icon(color='purple')).add_to(m2)

            # My route
            plugins.AntPath(route, weight=10, opacity=0.7, color = 'blue', tooltip = 'MI RUTA 🛣️').add_to(m2)
            plugins.AntPath(walk_route_2, weight=4, opacity=0.8, color = 'purple', tooltip = 'RUTA A PIE 🚶‍').add_to(m2)
            folium.Marker(route[0], tooltip = 'Inicio Ruta 🏠', icon = folium.Icon(color='blue', icon='home')).add_to(m2)
            folium.Marker(route[-1], tooltip = 'Final Ruta 🚩', icon = folium.Icon(color='blue', icon='flag')).add_to(m2)

            # Second choice
            folium.PolyLine(data_merged['Coordinates'][1], weight=5, opacity=0.9, color = 'green', tooltip = 'MATCH 🎉 ').add_to(m2)
            folium.Marker(data_merged['Coordinates'][1][0], tooltip = 'Inicio Ruta 🏠', icon = folium.Icon(color='green', icon ='home')).add_to(m2)
            folium.Marker(data_merged['Coordinates'][1][-1], tooltip = 'Final Ruta  🚩', icon = folium.Icon(color='green', icon ='flag')).add_to(m2)

            # Add layer control to show different maps
            folium.LayerControl().add_to(m2)
            folium_static(m2, width=1120)
            st.write('_Distancia a pie_ 🚶‍: ', np.round((dist_2),2), 'Kms')
            st.write('_Tiempo a punto de recogida_: ', int(np.round(minutes_2)), 'mins')

# =============================================================================
# Map 2 creation
# =============================================================================

    with tab2:
        url_1 = "https://geoportal.valencia.es/apps/OpenData/Trafico/tra_intensidad_trafico.json"
        df1 = pd.read_json(url_1)
        df_historic = pd.read_csv('/Users/diegoarcosdelasheras/Desktop/DATA SCIENCE/PROJECT/CSV_historic_traffic.csv')

        # Data cleaning process
        df_historic['IMD'] = df_historic['IMD'].apply(lambda x: x.replace(',', '.'))
        df_historic['IMD'] = df_historic['IMD'].apply(float)
        df_historic['IMD'] = df_historic['IMD'].apply(lambda x: int(x*1000))
        df_historic['PUNTO MUESTREO'] = df_historic["PUNTO MUESTREO"].str.strip(' ')

        area = df_historic.groupby(['PUNTO MUESTREO','LATITUD','LONGITUD'])['IMD'].mean()
        df_area = pd.DataFrame(area).reset_index()
        df_area['IMD'] = df_area['IMD'].apply(int)

        coordinates = []
        properties = []

        for i in df1.index:
            coor = df1['features'][i]['geometry']
            prop = df1['features'][i]['properties']
            coordinates.append(coor)
            properties.append(prop)

        data_cor = pd.DataFrame(coordinates).drop('type', axis = 1)
        data_prop = pd.DataFrame(properties)
        data_set = pd.concat([data_prop, data_cor], axis = 1)

        # Change values
        data_set.loc[(data_set['lectura'] == -1) | (data_set['lectura'] == 0), 'lectura'] = 1
        data = data_set.rename(columns = {'lectura':'transito (vh/h)'})

        # Folium part
        map = folium.Map(location=[39.4697500, -0.3773900], zoom_start=14, title = "Stamen Terrain")
        obj = LinearColormap([(0, 255, 0), (255, 165, 0), (255, 0, 0)])

        # Color Scale
        colormap = obj.scale(data['transito (vh/h)'].min(), data['transito (vh/h)'].max())
        colormap_2 = obj.scale(df_area['IMD'].min(), df_area['IMD'].max())
        colormap.caption = "Transito (vh/h)"
        colormap.add_to(map)

        # Points
        for path, traffic, des in zip(data['coordinates'], data['transito (vh/h)'], data['des_tramo']):
            points = [(i[1], i[0]) for i in path]
            folium.PolyLine(points, weight=10, opacity=0.5, color = colormap(traffic), tooltip = des).add_to(map)

        plugins.MiniMap(toggle_display = True, position="bottomleft").add_to(map)
        plugins.Fullscreen(position = 'topright').add_to(map)

        # Add tiles to map
        folium.raster_layers.TileLayer('Stamen Terrain').add_to(map)
        folium.raster_layers.TileLayer('Open Street Map').add_to(map)
        folium.raster_layers.TileLayer('Stamen Toner').add_to(map)
        folium.raster_layers.TileLayer('Stamen Watercolor').add_to(map)
        folium.raster_layers.TileLayer('CartoDB Positron').add_to(map)
        folium.raster_layers.TileLayer('CartoDB Dark_Matter').add_to(map)

        folium.LayerControl().add_to(map)
        folium_static(map, width=1120)
except:
    st.caption('')



