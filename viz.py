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
from dateConverter import DateConverter
from date import Date

dataDirectory = "VisitorLogs/"
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

def performCounts(masterData):
    cityCounts = {}
    for row in masterData.itertuples():
        if cityCounts.get(row.city) == None:
            cityCounts[row.city] = 1
        else:
            cityCounts[row.city] = cityCounts[row.city] + 1

    masterData['Dashboards uses in the city'] = masterData['city'].map(cityCounts)

    return masterData


def removePII(masterData):
    masterData = masterData.drop(columns=['ip_address', 'isp', 'success', 'iso3', 'timezone'])
    return masterData


def createDf(startDate, endDate):
    masterData = pd.DataFrame()

    startYear, startMonth = DateConverter.getMonthAndYear(startDate)
    endYear, endMonth = DateConverter.getMonthAndYear(endDate)

    for dir in listdir(dataDirectory):
        if dir >= str(startYear) and dir <= str(endYear):
            for subDir in listdir(dataDirectory + "/" + dir):
                if MONTHS.index(subDir) >= startMonth and MONTHS.index(subDir) <= endMonth:
                    for file in listdir(dataDirectory + "/" + dir + "/" + subDir):
                        df = pd.read_csv(dataDirectory + "/" + dir + "/" + subDir + "/" + file)
                        masterData = pd.concat([masterData, df])

    if masterData.empty:
        masterData = pd.DataFrame(columns=['city', 'country', 'latitude', 'longitude', 'Dashboards uses in the city'])
        return masterData

    masterData = masterData[masterData['dashboard'] != 'doesnotexist']
    masterData = removePII(masterData)

    return masterData


def createFig1(masterData, country=None):

    #This is bugged
    if masterData.empty or masterData.shape[0] == 0:
        fig1 =  px.density_mapbox(mapbox_style="stamen-toner")

    else:
        fig1 = px.density_mapbox(masterData, lat='latitude', lon='longitude', z='Dashboards uses in the city', radius=10,
                            center=dict(lat=43.6532, lon=79.3832), zoom=1,
                            mapbox_style="stamen-toner")

        if country != "":
            for row in masterData.itertuples():
                if row.country == country:
                    latitude = row.latitude
                    longitude = row.longitude

                    fig1 = px.density_mapbox(masterData, lat='latitude', lon='longitude', z='Dashboards uses in the city', radius=20,
                                        center=dict(lat=latitude, lon=longitude), zoom=4,
                                        mapbox_style="stamen-toner")

    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig1


def createDashboardChecklist(masterData):
    return dcc.Checklist(
        id='country-checklist',
        options=[{'label': i, 'value': i} for i in masterData['dashboard'].unique()],
        value=masterData['dashboard'].unique(),
        labelStyle={'display': 'inline-block', "display": "flex", "align-items": "center"},
        style={'width': '100%'}
    )


def createTable(masterData):
    return go.Figure(data=[go.Table(header=dict(values=masterData.columns),
                 cells=dict(values=masterData.transpose().values.tolist()))
                     ])


def removeDashboards(masterData, dashboards):
    masterData = masterData[masterData['dashboard'].isin(dashboards)]
    return masterData

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

masterData = createDf("2023 April", "2023 July")
masterData = performCounts(masterData)

fig1 = createFig1(masterData)

#Get the list of countries
countryList = masterData['country'].unique().tolist()

#Create a list of the dates
dateList = []
for year in os.listdir("VisitorLogs"):
    for month in os.listdir("VisitorLogs/" + year):
        dateList.append(DateConverter.convertYearAndMonth(int(year), month))
        # dateList.append(year + " " + month)

#Sort the list of dates
dateList.sort(key = lambda date: datetime.strptime(date, '%Y %B'))

#Create the table
table = createTable(masterData)

#Create the dashboard checklist
dashboardChecklist = createDashboardChecklist(masterData)

#Build a Plotly graph around the data
app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Where our users are'),

    dcc.Graph(figure=fig1, id="graph1"),

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


    html.H3(children='Dashboards'),
    dashboardChecklist,

    dcc.Graph(figure=table, id="table")
])



@app.callback(
    Output("end_date", "options"),
    Input("start_date", "value"))
def update_end_date(value):
    index = dateList.index(value)
    return dateList[index:]


@app.callback(
    Output("graph1", "figure"),
    Output("table", "figure"),
    Input("start_date", "value"),
    Input("end_date", "value"),
    Input("country_checklist", "value"),
    Input("country-checklist", "value")
    )
def updateGraph1(start, end, country, dashboards):
    masterData = createDf(start, end)

    masterData = removeDashboards(masterData, dashboards)
    performCounts(masterData)

    fig1 = createFig1(masterData, country)
    table = createTable(masterData)

    return fig1, table

if __name__ == '__main__':
    app.run_server(debug=False)