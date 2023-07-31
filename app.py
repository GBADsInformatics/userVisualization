# Census Data Quality Research
# Written By Ian McKechnie

import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from PIL import Image


from os import listdir
from dateConverter import DateConverter

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


def removeDashboardDupes(masterData):
    #Drop the '-V[0-9]+' from the dashboard name
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('-V[0-9]+', '')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('-v[0-9]+', '')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('v[0-9]+', '')
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('V[0-9]+', '')

    #rename laying-hens to layinghens
    masterData['Dashboard'] = masterData['Dashboard'].str.replace('laying-hens', 'layinghens')

    #Remove any Dashboards that are invalid
    invalidDashboards = ['Dashboards', 'somali-population']
    masterData = masterData[~masterData['Dashboard'].isin(invalidDashboards)]

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


def createGraph(masterData, country=None):
    latitude = 20
    longitude = 0
    zm = 0.75
    rds = 10

    if country != "":
        for row in masterData.itertuples():
            if row.Country == country:
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

oldestDate = "2023 April"
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

img = pil_image = Image.open("images/logo.png")

mostPopularDashboardname, mostPopularDashboardCount = mostPopularDashboard(masterData)
totalVisitCounts = countVisits(masterData)
totalCountries = countCountries(masterData)
uniqueDashboardCount = len(masterData['Dashboard'].unique())

# ---- Build the app ----

#Build a Plotly graph around the data
app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True
app.title = "GBADs Informatics User Vizualizer"

app.layout = html.Div(children=[
    html.Img(src=pil_image, style={'width': '25%', 'display': 'inline-block', "align-items": "left" }),
    html.H1(children='Where our users are'),

    html.H3(children=('The Global Burden for Animal Diseases (GBADs) dashboards have had ', totalVisitCounts, ' visits from ', totalCountries, ' unique countries.')),
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
                    countryList,
                    value="",
                    id="country-zoom",
                ),

            ], style={'width': '40%', 'display': 'inline-block', "align-items": "center" }),

            html.H3(children='Filters'),
            html.H4(children='Filter by date'),
            html.Div([
                html.Div([
                    html.H4(children='Start date'),
                    dcc.Dropdown(
                        options=[
                            {'label': date, 'value': date} for date in dateList
                        ],
                        value=dateList[0],
                        id="start_date",
                    ),
                ], style={'width': '80%', 'display': 'inline-block', "align-items": "center" }),

                html.Div([
                    html.H4(children='End date'),
                    dcc.Dropdown(
                        options=[
                            {'label': date, 'value': date} for date in dateList
                        ],
                        value=dateList[-1],
                        id="end_date",
                    ),
                ], style={'width': '80%', 'display': 'inline-block', "align-items": "center" })

            #align items horizontally
            ], style={'width': '40%', 'display': 'inline-block', "display": "flex", "align-items": "center", "justify-content": "space-between" }),

            html.H4(children='Filter by Dashboard'),
            html.H4(children='Dashboards'),
            dashboardChecklist,
        ])

    else:
        return html.Div([
            html.H3(children='Table of All Data'),
            dcc.Graph(figure=table, id="table", style={'width': '100%','height': '1000px', 'display': 'inline-block', "align-items": "center" }),
        ])


@app.callback(
    Output("end_date", "options"),
    Input("start_date", "value"))
def update_end_date(value):
    index = dateList.index(value)
    return dateList[index:]


@app.callback(
    Output("graph1", "figure"),
    # Output("table", "figure"),
    Input("start_date", "value"),
    Input("end_date", "value"),
    Input("country-zoom", "value"),
    Input("dashboard-checklist", "value")
    )
def updateGraph1(start, end, country, dashboards):
    masterData = createDf(start, end)

    if masterData.empty:
        fig1 = createGraph(masterData, country)
        # table = createTable(masterData)
        return fig1#, table

    masterData = removeDashboards(masterData, dashboards)
    performCounts(masterData)

    fig1 = createGraph(masterData, country)
    # table = createTable(masterData)

    return fig1#, table


if __name__ == '__main__':
    app.run_server(debug=True)