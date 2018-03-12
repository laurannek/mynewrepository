import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import requests
import folium
from folium import plugins
import plotly.plotly as py
from plotly.graph_objs import *

# Query Data from Redash

redash_cookie = (".eJwdjk1rwzAQRP9K2XMOsWRfDD24qAQHdoOFUrO6hHw4dlbRJabEUch_r5vjDG9484Td-daNA5Tn_XXsFrC7nKB8wscBSvCCCZUVv6o1umoi1-ecjgUlCuyOmhMvqW1yirX2zkZ224wia2_CnKuM1fcD2-0SFWbeNJraH_ESHhtT3Sl9hXmvUejK7hTJNJN3WKDYQNLrfy-ZWpHYiLG5s-Np7nNU9cyFzIsd0K0HlFCg6T_htYDfsbu9_4OC1x8b_ka1.DXHfHQ.vS33oG8xaCkPLd8vA11AzM0LMbU")

redash_query_dict = {
    "Where are the risk zones for theft and vandalism in campus?": 111,
    "Where are the bikes that can still be recovered outside of the Service Area?": 116,
    "Where were the bikes likely vandalized?": 117,
    "Where did the devices shutdown happened?": 118
}


  # Query the data via redash pre-processed queries

def query_redash(query_number):
    cookie = {'session': redash_cookie}
    url = 'https://redash.noa.one/api/queries/{}/results.json'.format(query_number)
    result_query = requests.get(url, cookies=cookie)
    parsed_result = result_query.json()['query_result']['data']['rows']
    df_result= pd.DataFrame(parsed_result)
    return df_result

    # Find the center of a group of coordinates in order to bring the Hea†map Focus where the data is

def center_of_points(list_of_coordinates):
    latitude = [latitude[0] for latitude in list_of_coordinates]
    longitude = [longitude[1] for longitude in list_of_coordinates]
    centroid = [sum(latitude) / len(list_of_coordinates), sum(longitude) / len(list_of_coordinates)]
    return centroid


    # Create Heatmap with Folium

def Heatmap(query_number, time_of_day, tracker_type):
    df_result= query_redash(query_number)
    df_result = df_result[df_result.longitude.notnull()]
    df_result_locations = df_result[['latitude','longitude']].values.tolist()
    heatmap= folium.Map(center_of_points(df_result_locations), zoom_start=10)
    if len(time_of_day) == 0 or tracker_type == None:
        df_result_timeofday = []
    else :
        df_result_timeofday = df_result[(df_result.time_of_day.isin(time_of_day)) & (df_result.tracker_type_check.isin(tracker_type))]
        df_result_timeofday_locations = df_result_timeofday[['latitude','longitude']].values.tolist()
        heatmap.add_child(plugins.HeatMap(df_result_timeofday_locations, radius=15))
    return heatmap._repr_html_()


    # Create a Scatter map with Folium

def ScatterMap(query_number, time_of_day, tracker_type):
    df_result = query_redash(query_number)
    df_result = df_result[df_result.longitude.notnull()]
    df_result_locations = df_result[['latitude','longitude']].values.tolist()
    scattermap = folium.Map(center_of_points(df_result_locations), zoom_start=10) #, tiles='Stamen Toner'
    if len(time_of_day) == 0 or tracker_type == None:
        df_result_timeofday = []
    else :
        df_result_timeofday = df_result[(df_result.time_of_day.isin(time_of_day)) & (df_result.tracker_type_check.isin(tracker_type))]
        for idx, row in enumerate(df_result_timeofday.itertuples()):
                folium.CircleMarker([row.latitude, row.longitude], radius=1, popup='bike_uuid: ' + str(row.bicycle_uuid) + '\n timestamp: '+ str(row.timestamp), color = '#260c0c' ).add_to(scattermap)  # can add : + '\n timestamp: '+ str(row.timestamp_lp))
    return scattermap._repr_html_()


app = dash.Dash()


app.layout = html.Div(children = [
    html.Div(children = [
        html.Label('Lost Bikes Vizualisation - Google'),
        dcc.Dropdown(
            id = 'query-dropdown',
            options = [{'label': key, 'value': value} for key, value in redash_query_dict.items()],
            value=111),

        html.Label('Choose Map Type'),
        dcc.RadioItems(
           id = 'maptype-radioitem',
           options = [{'label': 'HeatMap' , 'value': 'HeatMap'},
                      {'label': 'ScatterMap' , 'value': 'ScatterMap'}
                      ],
           value = 'ScatterMap'
    )

    ], style = {'width': '50%', 'display': 'inline-block'}),
    html.Iframe(id = 'map', srcDoc = None, height = '430', width = '50%'),
html.Div( children = [
    dcc.Dropdown(
        id = 'timeofday--picker',
        options = [{'label': 'Morning', 'value': 0},
                   {'label': 'Afternoon', 'value': 1},
                   {'label': 'Evening', 'value': 2},
                   {'label': 'Night', 'value': 3}
                ],
        multi = True,
        value = [0,1,2,3]
                ),
    dcc.Checklist(
        id = 'tracker_type--checkbox',
        options = [{'label': 'Donut', 'value': 'Donut'},
                 {'label': 'Mercury', 'value': 'Mercury'}
                ],
                values = ['Donut'],
                labelStyle = {'display': 'inline-block'}
            )
    ], style = {'width': '50%', 'display': 'inline-block'}
    )
])

# Callback the Heatmap whenever there is an Input
@app.callback(
    Output(component_id = 'map', component_property = 'srcDoc'),
    [Input(component_id = 'query-dropdown', component_property = 'value'),
     Input(component_id = 'maptype-radioitem', component_property = 'value'),
     Input(component_id = 'timeofday--picker', component_property = 'value'),
     Input(component_id = 'tracker_type--checkbox', component_property = 'values')]
)
def update_map(query_number, map_type, time_of_day, tracker_type):
    if  map_type == 'HeatMap':
        maptype = Heatmap(query_number, time_of_day, tracker_type)
    else:
        maptype = ScatterMap(query_number, time_of_day, tracker_type)
    return maptype
    #return ["hello"]

# NOTE: port set so it doesn't conflict with open notebooks during development
if __name__ == '__main__':
    app.run_server(debug=True, port= 8076)
