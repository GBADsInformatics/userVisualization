# Census Data Quality Research
# Written By Ian McKechnie

import sys
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from os import listdir
from os.path import isfile, join

dataDirectory = "VisitorLogs/"
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

#Set the default date ranges
availableYears = [i for i in range(2020, datetime.now().year)]
availableMonths = [i for i in range(1, 13)]

defaultYear = availableMonths[-1]
# defaultMonth = datetime.now().month #Uses the current month as the default month
defaultMonth = 7 #Uses the current month as the default month


print(defaultMonth)
print("dir = " + dataDirectory + MONTHS[defaultMonth -1] )
#Get the data from the csv files
masterData = pd.DataFrame()
onlyfiles = [f for f in listdir(dataDirectory + MONTHS[defaultMonth -1] ) if isfile(join(dataDirectory + MONTHS[defaultMonth -1] , f))]

for file in onlyfiles:
    print("Really before file = " + dataDirectory + MONTHS[defaultMonth -1] + "/" + file)

    df = pd.read_csv(dataDirectory + MONTHS[defaultMonth -1] + "/" + file)

    print("Before")
    masterData = pd.concat([masterData, df])
    print("After")

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


#start Months list
startMonths = [i for i in range(1, 13)]

#Build a Plotly graph around the data
app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Where our users are'),

    dcc.Graph(figure=fig1),

    dcc.Graph(figure=fig2),


    html.H3(children='Countries'),
    # dcc.Dropdown(
    #     countries,
    #     value=countries[0],
    #     id="country_checklist",
    # ),

    html.H3(children='Filters'),

    html.H4(children='Start Month'),
    dcc.Dropdown(

    # dcc.Dropdown(
    #     species,
    #     value=species[0],
    #     id="species_checklist",
    # ),
])

# @app.callback(
#     Output("species_checklist", "options"),
#     Input("country_checklist", "value"))
# def update_species_checklist(country):
#     # Step one: Get FAO data
#     species = ["Cattle","Sheep","Goats","Pigs","Chickens"]

#     # Step 3: Get Census data
#     try:
#         csv_data = pd.read_csv(f"censusData/{country}.csv")
#         species = species + csv_data["species"].tolist() # Add the species from the csv file to the list of species
#         species = list(dict.fromkeys(species))  # Remove duplicates from the list of species

#     except:
#         print("Error, count not find the correct csv file")

#     # Step 4: Get National data
#     try:
#         nationalData = pd.read_csv(f"nationalData/{country}.csv")
#         species = species + nationalData["species"].tolist() # Add the species from the csv file to the list of species
#         species = list(dict.fromkeys(species))  # Remove duplicates from the list of species

#     except:
#         print("Error, count not find the correct csv file")

#     return species

# @app.callback(
#     Output("graph", "figure"),
#     Input("species_checklist", "value"),
#     Input("country_checklist", "value"))
# def update_line_chart(specie, country):
#     # Step one: Get FAO data
#     countries = ["Greece", "Ethiopia", "Canada", "USA", "Ireland", "India", "Brazil", "Botswana", "Egypt", "South Africa", "Indonesia", "China", "Australia", "NewZealand", "Japan", "Mexico", "Argentina", "Chile"]
#     species = ["Cattle","Sheep","Goats","Pigs","Chickens"]

#     if specie == None:
#         specie = species[0]

#     if country == "USA":
#         fao_data = fao.get_data("United%20States%20of%20America", specie)

#     elif country == None:
#         fao_data = fao.get_data(countries[0], specie)

#     else:
#         fao_data = fao.get_data(country, specie)

#     fao_data = fao.formatFAOData(fao_data)

#     # Step two: Get woah data
#     if country == "USA":
#         woah_data = woah.get_data("United%20States%20of%20America", specie)
#     else:
#         woah_data = woah.get_data(country, specie)

#     woah_data = woah.formatWoahData(woah_data)

#     # Step 3: Get Census data
#     csv_data, csv_index_list, species = API_helpers.helperFunctions.getFormattedCensusData(country, specie, species)

#     # Step 4: Get National data
#     nationalData, nationalData_index_list, species = API_helpers.helperFunctions.getFormattedNationalData(country, specie, species)

#     # Build a master dataframe
#     #master_df = pd.concat([fao_data, woah_data, csv_data.iloc, nationalData.iloc])
#     master_df = pd.concat([fao_data, woah_data, csv_data.iloc[csv_index_list], nationalData.iloc[nationalData_index_list]])

#     # Build the plotly graph
#     fig = px.line(
#             master_df,
#             x=master_df["year"],
#             y=master_df["population"],
#             color=master_df["source"],
#             markers=True)

#     fig.update_yaxes(
#         type='linear',
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey'
#     )

#     fig.update_xaxes(
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey'
#     )


#     fig.update_traces(line=dict(width=5))

#     fig.update_layout(
#         title=f"Population of {specie} in {country}",
#         xaxis_title="Year",
#         yaxis_title="Population",
#         legend_title="Sources",
#         font = dict(
#             size=18,
#         ),
#         plot_bgcolor='white',
#     )
#     return fig

if __name__ == '__main__':
    app.run_server(debug=True)