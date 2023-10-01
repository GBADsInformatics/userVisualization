# Census Data Quality Research
# Written By Ian McKechnie

import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from PIL import Image
from flask import Flask, redirect
from os import listdir
from dateConverter import DateConverter
import re

# Get app base URL
BASE_URL = os.getenv('BASE_URL','/')

dataDirectory = "VisitorLogs/"
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
countryCenters = {
    "United States of America (the)": {"lat": 39.8282, "lon": -98.5796, "zoom": 3},
    "Canada": {"lat": 56.1304, "lon": -106.3468, "zoom": 2.5},
    "Australia": {"lat": -25.2744, "lon": 133.7751, "zoom": 3},
    "Russian Federation (the)": {"lat": 61.5240, "lon": 105.3188, "zoom": 2},
    "Brazil": {"lat": -14.2350, "lon": -51.9253, "zoom": 2.5},
    "India": {"lat": 20.5937, "lon": 78.9629, "zoom": 2.5},
    "China": {"lat": 35.8617, "lon": 104.1954, "zoom": 2.5},
    "United Kingdom of Great Britain and Northern Ireland (the)": {"lat": 55.3781, "lon": -3.4360, "zoom": 4},
    "Mexico": {"lat": 23.6345, "lon": -102.5528, "zoom": 2.5},
}

def countMonths():
    count = 0
    for year in listdir(dataDirectory):
        for month in listdir(dataDirectory + "/" + year):
            count = count + 1

    return count


def createGraph(masterData, country=None):
    latitude = 20
    longitude = 0
    zm = 0.75
    rds = 10

    if country != "":
        for row in masterData.itertuples():
            if row.Country == country:
                hit = True
                if country in countryCenters:
                    latitude = countryCenters[country]["lat"]
                    longitude = countryCenters[country]["lon"]
                    zm = countryCenters[country]["zoom"]

                else:
                    latitude = row.Latitude
                    longitude = row.Longitude
                    zm = 4

    graph = px.density_mapbox(masterData,
        lat='Latitude',
        lon='Longitude',
        z='Dashboards viewed in this city',
        radius=rds,
        center=dict(lat=latitude, lon=longitude),
        zoom=zm,
        mapbox_style="stamen-toner")

    graph.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return graph


def performCounts(masterData):
    cityCounts = {}
    for row in masterData.itertuples():
        if cityCounts.get(row.City) == None:
            cityCounts[row.City] = 1
        else:
            cityCounts[row.City] = cityCounts[row.City] + 1

    masterData['Dashboards viewed in this city'] = masterData['City'].map(cityCounts)

    return masterData


def removePII(masterData):
    if 'Success' in masterData.columns:
        masterData = masterData.drop(columns=['Success'])

    return masterData.drop(columns=['Ip_address', 'Isp', 'Timezone', 'Localtime'])


def remove_version_strings(input_string):
    pattern =  r'[-]?[vV]\d+'
    return re.sub(pattern, '', input_string)


def removeDashboardDupes(masterData):
    #Drop the '-V[0-9]+' from the dashboard name
    masterData['Dashboard'] = masterData['Dashboard'].apply(remove_version_strings)

    #rename laying-hens to layinghens
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Laying-hens', 'Layinghens')

    masterData = renameDashboards(masterData)

    #Remove any Dashboards that are invalid
    invalidDashboards = ['Dashboards', 'Somali-population', 'Non-existent']
    masterData = masterData[~masterData['Dashboard'].isin(invalidDashboards)]

    return masterData


def renameDashboards(masterData):
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Ahle', 'Animal Health Loss Envelope')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Apiui', 'GBADs API Explorer')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Biomass', 'Livestock Biomass')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Datastories', 'Ethiopia Data Stories')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Ethiopia-population', 'Ethiopia Sub-National Population')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Layinghens', 'Layinghens Visualization')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Population', 'National Population')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Tev', 'Total Economic Value')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('Visualizer', 'Data Visualizer')

    return masterData


def removeUnsuccessfulConnections(masterData):
    if 'Success' not in masterData.columns:
        return masterData

    return masterData[masterData['success'] == 200]


def createDf(startDate, endDate):
    masterData = pd.DataFrame()

    startYear, startMonth = DateConverter.getMonthAndYear(startDate)
    endYear, endMonth = DateConverter.getMonthAndYear(endDate)

    for dir in listdir(dataDirectory):
        if dir >= str(startYear) and dir <= str(endYear):
            for subDir in listdir(dataDirectory + "/" + dir):
                if MONTHS.index(subDir) >= startMonth and MONTHS.index(subDir) <= endMonth:
                    for file in listdir(dataDirectory + "/" + dir + "/" + subDir):
                        df = pd.read_csv(dataDirectory + "/" + dir + "/" + subDir + "/" + file, on_bad_lines='skip')
                        masterData = pd.concat([masterData, df])

    if masterData.empty:
        masterData = pd.DataFrame(columns=['City', 'Country', 'Latitude', 'Longitude', 'Dashboards viewed in this city'])
        return masterData

    masterData = masterData[masterData['dashboard'] != 'doesnotexist']

    #Capitalize the Dashboard names
    masterData['dashboard'] = masterData['dashboard'].str.capitalize()

    #Capitalize the columns
    masterData.columns = map(str.capitalize, masterData.columns)

    masterData = removePII(masterData)
    masterData = removeDashboardDupes(masterData)
    masterData = removeUnsuccessfulConnections(masterData)

    return masterData


def createDfWithOnlyDate(date):
    masterData = pd.DataFrame()

    year, month = DateConverter.getMonthAndYear(date)
    dir = dataDirectory + str(year) + "/" + MONTHS[month]

    for file in listdir(dir):
        df = pd.read_csv(dir + "/" + file)
        masterData = pd.concat([masterData, df])


    if masterData.empty:
        masterData = pd.DataFrame(columns=['City', 'Country', 'Latitude', 'Longitude', 'Dashboards viewed in this city'])
        return masterData

    masterData = masterData[masterData['dashboard'] != 'doesnotexist']

    #Capitalize the Dashboard names
    masterData['dashboard'] = masterData['dashboard'].str.capitalize()

    #Capitalize the columns
    masterData.columns = map(str.capitalize, masterData.columns)

    masterData = removePII(masterData)
    masterData = removeDashboardDupes(masterData)

    return masterData


def createDashboardChecklist(masterData):
    sortedDashboardList = masterData['Dashboard'].unique().tolist()
    sortedDashboardList.sort()

    return dcc.Checklist(
        id='dashboard-checklist',
        # options=[{'label': i, 'value': i} for i in masterData['dashboard'].unique()],
        options=[{'label': i, 'value': i} for i in sortedDashboardList],
        value=masterData['Dashboard'].unique(),
        labelStyle={'display': 'inline-block', "display": "flex", "align-items": "center"},
        style={'width': '100%'},
    )


def createTable(masterData):
    return go.Figure(data=[
                go.Table(
                    header=dict(
                        values=masterData.columns,
                        fill_color='lightgrey',
                        align='center',
                        ),
                    cells=dict(
                        values=masterData.transpose().values.tolist(),
                        fill_color='white',
                        align='center',
                        ))])


def removeDashboards(masterData, dashboards):
    masterData = masterData[masterData['Dashboard'].isin(dashboards)]
    return masterData


def getDashboardCountsDict(masterData):
    dashboardCounts = {}
    for row in masterData.itertuples():
        if dashboardCounts.get(row.Dashboard) == None:
            dashboardCounts[row.Dashboard] = 1
        else:
            dashboardCounts[row.Dashboard] = dashboardCounts[row.Dashboard] + 1

    return dashboardCounts


def mostPopularDashboard(masterData):
    #find the most popular dashboard and its count
    dashboardCounts = getDashboardCountsDict(masterData)

    mostPopularDashboard = max(dashboardCounts, key=dashboardCounts.get)
    mostPopularDashboardCount = dashboardCounts[mostPopularDashboard]

    return mostPopularDashboard, mostPopularDashboardCount


def countVisits(masterData):
    dashboardCounts = getDashboardCountsDict(masterData)

    totalVisits = 0
    for dashboard in dashboardCounts:
        totalVisits = totalVisits + dashboardCounts[dashboard]

    return totalVisits


def countCountries(masterData):
    return len(masterData['Country'].unique())


def createDashboardLinks():
    return html.Div([
        html.A('Animal Health Loss Envelope', href='https://gbadske.org/dashboards/ahle/', target='_blank'),
        html.A('GBADs API Explorer', href='https://gbadske.org/dashboards/apiui/', target='_blank'),
        html.A('Livestock Biomass', href='https://gbadske.org/dashboards/biomass/', target='_blank'),
        html.A('Ethiopia Data Stories', href='https://gbadske.org/dashboards/datastories/', target='_blank'),
        html.A('Ethiopia Sub-National Population', href='https://gbadske.org/dashboards/datastories/', target='_blank'),
        html.A('Layinghens Visualization', href='https://gbadske.org/dashboards/layinghens/', target='_blank'),
        html.A('National Population', href='https://gbadske.org/dashboards/population/', target='_blank'),
        html.A('Total Economic Value', href='https://gbadske.org/dashboards/tev/', target='_blank'),
        html.A('Data Visualizer', href='https://gbadske.org/dashboards/visualizer/', target='_blank'),
    ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'left'})


oldestDate = "2023 May"
currentDate = datetime.now().strftime("%Y %B")

masterData = createDf(oldestDate, currentDate)
masterData = performCounts(masterData)

fig1 = createGraph(masterData)

#Get the list of countries
countryList = masterData['Country'].unique().tolist()
countryList.sort()

#Create a list of the dates
dateList = []
for year in os.listdir("VisitorLogs"):
    for month in os.listdir("VisitorLogs/" + year):
        dateList.append(DateConverter.convertYearAndMonth(int(year), month))

#Sort the list of dates
dateList.sort(key = lambda date: datetime.strptime(date, '%Y %B'))

#Create the table
table = createTable(masterData)

#Create the dashboard checklist
dashboardChecklist = createDashboardChecklist(masterData)

#Dashboard hyperlinks
dashboardLinks = createDashboardLinks()

img = pil_image = Image.open("images/logo.png")

mostPopularDashboardname, mostPopularDashboardCount = mostPopularDashboard(masterData)
totalVisitCounts = countVisits(masterData)
totalCountries = countCountries(masterData)
uniqueDashboardCount = len(masterData['Dashboard'].unique())
monthsElapsed = countMonths()

# ---- Build the app ----

#Build a Plotly graph around the data
app = Dash(__name__, requests_pathname_prefix=os.getenv('BASE_URL', '')+'/')
app.config["suppress_callback_exceptions"] = True
app.title = "GBADs Informatics User Vizualizer"

app.layout = html.Div(children=[
    html.Img(src=pil_image, style={'width': '25%', 'display': 'inline-block', "align-items": "left" }),
    html.H1(children='Where our users are'),

    html.H3(children=('The Global Burden for Animal Diseases (GBADs) dashboards have had ', totalVisitCounts, ' visits from ', totalCountries, ' unique countries over ', monthsElapsed, ' months.')),
    html.H3(children=('Our most popular dashboard is ', mostPopularDashboardname, ' which has had ', mostPopularDashboardCount, ' total views.')),
    html.H3(children=('GBADs currently offers ', uniqueDashboardCount, ' unqiue dashboards.')),

    dcc.Tabs(id="tabs", value='graph-tab', children=[
        dcc.Tab(label='Interactive Map', value='graph-tab'),
        dcc.Tab(label='Table of data', value='table-tab'),
    ]),
    html.Br(),
    html.Div(id='contents'),
])


# ---- Callbacks ----
@app.callback(
        Output('contents', 'children'),
        Input('tabs', 'value'))
def render_content(tab):
    if tab == 'graph-tab':
        return html.Div([
            dcc.Graph(figure=fig1,
                      id="graph1",
                      style={'width': '100%', 'display': 'inline-block', "align-items": "center" }),

            html.Div([

                html.H3(children='Zoom in on a country'),
                dcc.Dropdown(
                    options=countryList,
                    value="",
                    id="country-zoom",
                ),

            ], style={'width': '40%', 'display': 'inline-block', "align-items": "center" }),

            html.H3(children='Filters'),
            html.H4(children='Filter by months since tracking'),
            html.Div([
                dcc.Slider(
                    0,
                    len(dateList) - 1,
                    step=None,
                    value=0,
                    marks={dateList.index(date): date for date in dateList},
                    id='date-slider'
                )

            #align items horizontally
            ], style={'width': '40%', 'display': 'inline-block', "align-items": "center"}),

            html.H4(children='Filter by Dashboard'),

            html.Div([
                html.Div([
                    html.H4(children='Dashboards'),
                    dashboardChecklist,
                ], style={"padding-right": "100px"}),
                html.Div([
                    html.H4(children='Links to Dashboards'),
                    dashboardLinks
                ])

            #align items horizontally
            ], style={'width': '50%', 'display': 'inline-block', "display": "flex", "align-items": "center" }),
        ])

    else:
        return html.Div([
            html.H3(children='Table of All Data'),
            dcc.Graph(figure=table, id="table", style={'width': '100%','height': '1000px', 'display': 'inline-block', "align-items": "center" }),
        ])


@app.callback(
    Output("graph1", "figure"),
    Input("date-slider", "value"),
    Input("country-zoom", "value"),
    Input("dashboard-checklist", "value")
)
def updateGraph1(date, country, dashboards):
    masterData = createDfWithOnlyDate(dateList[date])

    if masterData.empty:
        return createGraph(masterData, country)

    masterData = removeDashboards(masterData, dashboards)
    performCounts(masterData)

    return createGraph(masterData, country)


@app.callback(
    Output("country-zoom", "options"),
    Input("date-slider", "value"),
)
def updateCountryDropDown(date):
    masterData = createDfWithOnlyDate(dateList[date])

    if masterData.empty:
        return []

    options = masterData['Country'].unique().tolist()
    options.sort()

    return options


if __name__ == '__main__':
    app.run_server(debug=True)

def returnApp():
    """
    This function is used to create the app and return it to waitress in the docker container
    """
    # If BASE_URL is set, use DispatcherMiddleware to serve the app from that path
    if 'BASE_URL' in os.environ:
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        app.wsgi_app = DispatcherMiddleware(Flask('dummy_app'), {
            os.environ['BASE_URL']: app.server
        })
        # Add redirect to new path
        @app.wsgi_app.app.route('/')
        def redirect_to_dashboard():
            return redirect(os.environ['BASE_URL'])
        return app.wsgi_app

    # If no BASE_URL is set, just return the app server
    return app.server