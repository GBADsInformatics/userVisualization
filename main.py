import duckdb
import pandas as pd
import sys
import os
import datetime
import calendar
import boto3
import S3TicketLib as s3f
import downloadVLogs as down
​
#
# Demo program that shows how to copy dashboard visit logs from S3 to 
# a local directory named after the month requested
#     python3 monthlyDuck.py YYYY MM 
# where YYYY is year and MM is month from 01 to 12 (must include the
# leading zero)
# Example
#     python3 monthlyDuck.py 2023 06 
#     - will download all the files from 20230601 to 20230630 and puts them
#       in the local subdirectory ./June
#     - reates local subdirectory if it does not exist
#     - rest of script analyzes/reports on various interesting statistics/information
#         - when calculating the number of unique users/ips, locations, etc. this only consists
#           this one month and is not cumulative over the preceeding months which it
#           should eventually do (need to store certain information about users/ips, locations,
#           dashboard accesses probably on S3)
#     - not all columns are used in the following code, e.g. latitude and longitude and success code
#     - as of 20230628, the success codes are unreliable and should not be used yet
​
# Following function identifies start and end dates for weeks in the
# month begin examined
def weeks ( y, m ):
    weekStart = []
    weekEnd = []
    weekDates = []
    cld = calendar.Calendar(firstweekday=0)
    for end_day in cld.itermonthdates(y,m):
        if end_day.weekday() == 5:
            start_day = end_day-datetime.timedelta(6)
            weekStart.append(format(start_day.isoformat()))
            weekEnd.append(format(end_day.isoformat()))
    weekDates = [ weekStart, weekEnd ]
    return weekDates
​
# Number of days in each month (February has 29 in case of a leap year)
last_day = [ 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]
# Months of the Year
month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December' ]
​
# Get date information from the command line
#    - the mm ( month ) number should be padded with a zero to the left
#      if it is only 1 character long
yyyy = sys.argv[1]
mm = sys.argv[2]
if len(mm) == 1:
    mm = "0"+mm
mon = int(mm) - 1
start_date = yyyy+mm+"01"
end_date = yyyy+mm+str(last_day[mon])
yyyyStartStr = yyyy + "-01-01 00:00:00"
yyyyEndStr = yyyy + "-12-31 23:59:59"
​
#  Access AWS Credentials and establish session
#  as a client
#
s3_client = s3f.credentials_client ( )
#
#  Access AWS Credentials and establish session
#  as a resource
#
s3_resource = s3f.credentials_resource ( )
​
# Download a month of visitor logs
#
# Create a local directory if it does not exist
localpath = "./"+month_names[mon]
if os.path.exists(localpath) == False:
    os.mkdir(localpath)
# Download the files from S3 and put them in the local directory
localdir = month_names[mon]+"/"
ret = down.downloadVLogs ( s3_client, s3_resource, "gbads-aws-access-logs", "VisitorLogs/", start_date, end_date, localdir )
# downloSVLogs return 0 if successful and -1 on failure
if ret != 0:
    print ( "Could not download the month stats" )
    exit ( -1 )
# Read in a month of visitor logs into DuckDB
log_names = month_names[mon]+"/VISITOR_LOGS*.csv"
visits = duckdb.query( f"SELECT * FROM read_csv_auto('{log_names}', header=True)").to_df()
​
# Gather some Month stats
#     Number of visits to the dashboards
month_stats = duckdb.query ( f"SELECT date,ip_address,iso3,country,city,dashboard FROM visits WHERE date BETWEEN '{yyyyStartStr}' AND '{yyyyEndStr}' " ).to_df()
print ( "Statistics for "+month_names[mon]+" "+yyyy )
print ( "There were "+str(len(month_stats))+" visits to the Dashboards" )
​
#     Number of distinct IP's that visited the dashboards
ips = duckdb.query ( "SELECT DISTINCT ip_address FROM month_stats ORDER BY ip_address" ).to_df()
print ( str(len(ips))+" unique users accessed the Dashboards")
print ( "----------")
​
#     Number of unique locations (city, country) that visited the dashboards
#         - the names for the United States and the United Kingdom are too long so replace with short forms
locations = duckdb.query ( "SELECT DISTINCT iso3,country,city FROM month_stats ORDER BY country,city" ).to_df()
print ( "The Dashboards were accessed from "+str(len(locations))+" unique locations:" )
for index, row in locations.iterrows():
    print(row['city'],end=", ")
    if row['iso3'] == "USA":
        print("USA")
    elif row['iso3'] == "GBR":
        print("UK")
    else:
        print(row['country'])
print ( "----------")
​
#     Number of distinct dashboards visited and the number of visits
#          Dashboards Information
#          - to find out what dashboards exist, read the dashboard
#            information in from the file dashboards.csv which contains
#            short_name,long_name,start_date,end_date
#
# Valid dashboards in the system 
valid_df = duckdb.query( f"SELECT short_name FROM read_csv_auto('dashboards.csv', header=True)").to_df()
validDashs = valid_df["short_name"].values.tolist()
#print ( validDashs )
dashs = duckdb.query ( "SELECT DISTINCT dashboard FROM month_stats ORDER BY dashboard" ).to_df()
print ( "There were "+str(len(dashs))+" unique dashboards accesses attempted of which " )
valid = 0
invalid = 0
validDash = []
invalidDash = []
for index, row in dashs.iterrows():
    if row['dashboard'] in validDashs:
        validDash.append(row['dashboard'])
        valid = valid + 1
    else:
        invalidDash.append(row['dashboard'])
        invalid = invalid + 1
if valid > 1:
    print ( str(valid)+" were valid: " )
else:
    print ( str(valid)+" was valid: " )
​
for i in validDash:
    print ( "    "+i )
if invalid > 1:
    print ( "and "+str(len(invalidDash))+" were invalid:" )
else:
    print ( "and "+str(len(invalidDash))+" was invalid:" )
for i in invalidDash:
    print ( "    "+i )
print ( "----------")
​
ctdashs = duckdb.query ( "SELECT DISTINCT dashboard, count(dashboard) FROM month_stats GROUP BY dashboard" ).to_df()
print ( ctdashs )
print ( "----------")
​
#     Display information by week
#         Notes
#         - since some weeks have days in other months, this code ignores those days
#         - this code also shows a different methodology for calculating the number
#           of unique visitors by the use of sets
startEnd = weeks ( int(yyyy), int(mm) )
week = []
weeks = []
wx = {}
for i in range (0, len(startEnd[0])):
    sweek = startEnd[0][i]+" 00:00:00"
    eweek = startEnd[1][i]+" 23:59:59"
    wk = duckdb.sql ( f"SELECT DISTINCT ip_address FROM visits WHERE date BETWEEN '{sweek}' AND '{eweek}'" ).to_df()
    w = wk['ip_address'].tolist()
    weeks.append(w)
    print ( f"There were "+str(len(weeks[i]))+f" unique visitors for the week {startEnd[0][i]} to {startEnd[1][i]}" )
    #print ( weeks[i] )
    #print ( "----------")
    if i > 0:
        w1 = set(weeks[i-1]).union(wx)
        w2 = set(weeks[i])
        #w3 = w1.union(wx)
        #w1 = w3
        wx = w1
        wdiff = w2.difference(w1)
        diff = list(wdiff)
        print ( "Number of new users: "+str(len(diff)))
w1 = w2.union(wx)
print ( "Number of unique users over the month: "+str(len(w1)))