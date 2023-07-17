# Census Data Quality Research
# Written By Ian McKechnie

import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from os import listdir
from os.path import isfile, join

def createDf(StartYYYYMM, endYYYYMM):
    #Create a dataframe for the data
    df = pd.DataFrame()

    #Get the list of files
    onlyfiles = [f for f in listdir(dataDirectory + str(defaultYear) + "/" + MONTHS[defaultMonth -1] ) if isfile(join(dataDirectory + str(defaultYear) + "/" + MONTHS[defaultMonth -1] , f))]

    #Loop through the files and add them to the dataframe
    for file in onlyfiles:
        df = pd.concat([df, pd.read_csv(dataDirectory + str(defaultYear) + "/" + MONTHS[defaultMonth -1] + "/" + file)])

    #Return the dataframe
    return df

dataDirectory = "VisitorLogs/"
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

#Set the default date ranges
availableYears = [i for i in range(2020, datetime.now().year)]
availableMonths = [i for i in range(1, 13)]

defaultYear = 2023
# defaultMonth = datetime.now().month #Uses the current month as the default month
defaultMonth = 7 #Uses the current month as the default month

#Get the data from the csv files
masterData = pd.DataFrame()
onlyfiles = [f for f in listdir(dataDirectory + str(defaultYear) + "/" + MONTHS[defaultMonth -1] ) if isfile(join(dataDirectory + str(defaultYear) + "/" + MONTHS[defaultMonth -1] , f))]

for file in onlyfiles:
    df = pd.read_csv(dataDirectory + str(defaultYear) + "/" + MONTHS[defaultMonth -1] + "/" + file)
    masterData = pd.concat([masterData, df])

# while True:
#     try:
#         onlyfiles = [f for f in listdir(dataDirectory + MONTHS[defaultMonth -1] ) if isfile(join(dataDirectory + MONTHS[defaultMonth -1] , f))]

#         for file in onlyfiles:

#             print("Really before file = " + dataDirectory + MONTHS[defaultMonth -1] + "/" + file)

#             df = pd.read_csv(dataDirectory + MONTHS[defaultMonth -1] + "/" + file)

#             print("Before")
#             masterData = pd.merge(masterData, df, how='outer')
#             print("After")

#         break
#     except:
#         print("Need to download the data for this month")
#         quit()

##Need to add the quantity of each city to itself
cityCounts = {}
for row in masterData.itertuples():
    if cityCounts.get(row.city) == None:
        cityCounts[row.city] = 1
    else:
        cityCounts[row.city] = cityCounts[row.city] + 1

masterData['counts'] = masterData['city'].map(cityCounts)

fig1 = px.scatter_geo(masterData, lon="longitude", lat="latitude", color="city",
                     hover_name="city", size="counts",
                     projection="natural earth")
fig1.update_layout(mapbox_style="stamen-terrain", mapbox_center_lon=180)
fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


fig2 = px.density_mapbox(masterData, lat='latitude', lon='longitude', z='counts', radius=10,
                        center=dict(lat=43.6532, lon=79.3832), zoom=1,
                        mapbox_style="stamen-terrain")
fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


#Get the list of countries
countryList = masterData['country'].unique().tolist()

#Create a list of the dates
dateList = []
for year in os.listdir("VisitorLogs"):
    for month in os.listdir("VisitorLogs/" + year):
        dateList.append(year + " " + month)

#Sort the list of dates
dateList.sort(key = lambda date: datetime.strptime(date, '%Y %B'))

#Build a Plotly graph around the data
app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Where our users are'),

    dcc.Graph(figure=fig1, id="graph1"),

    dcc.Graph(figure=fig2, id="graph2"),

    html.H3(children='Zoom in on a country'),
    dcc.Dropdown(
        countryList,
        value="",
        id="country_checklist",
    ),

    html.H3(children='Filters'),
    html.H4(children='Start date'),
    dcc.Dropdown(
        options=[
            {'label': date, 'value': date} for date in dateList
        ],
        value=dateList[0],
        id="start_date",
    ),

    html.H4(children='End date'),
    dcc.Dropdown(
        options=[
            {'label': date, 'value': date} for date in dateList
        ],
        value=dateList[-1],
        id="end_date",
    ),
])


@app.callback(
    Output("graph2", "figure"),
    Input("country_checklist", "value"))
def countryZoomIn(country):

    fig2 = px.density_mapbox(masterData, lat='latitude', lon='longitude', z='counts', radius=10,
                        center=dict(lat=43.6532, lon=79.3832), zoom=1,
                        mapbox_style="stamen-terrain")

    for row in masterData.itertuples():
        if row.country == country:
            latitude = row.latitude
            longitude = row.longitude

            fig2 = px.density_mapbox(masterData, lat='latitude', lon='longitude', z='counts', radius=20,
                                center=dict(lat=latitude, lon=longitude), zoom=4,
                                mapbox_style="stamen-terrain")

    fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig2


@app.callback(
    Output("end_date", "options"),
    Input("start_date", "value"))
def update_end_date(value):

    index = dateList.index(value)

    updateGraph1(dateList[index:])
    updateGraph2(dateList[index:])

    return dateList[index:]


@app.callback(
    Output("graph1", "figure")
)
def updateGraph1(range):
    fig1 = px.scatter_geo(masterData, lon="longitude", lat="latitude", color="city",
                     hover_name="city", size="counts",
                     projection="natural earth")
    fig1.update_layout(mapbox_style="stamen-terrain", mapbox_center_lon=180)
    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig1


@app.callback(
    Output("graph2", "figure")
)
def updateGraph2(range):
    fig2 = px.density_mapbox(masterData, lat='latitude', lon='longitude', z='counts', radius=10,
                        center=dict(lat=43.6532, lon=79.3832), zoom=1,
                        mapbox_style="stamen-terrain")
    fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig2



if __name__ == '__main__':
    app.run_server(debug=True)