from os import listdir, remove, rmdir
from os.path import isfile, join

print("Cleaning...")
dataDirectory = "VisitorLogs/"

years = [f for f in listdir(dataDirectory )]
for year in years:

    months = [f for f in listdir(dataDirectory + "/" + year)]

    for month in months:
        dir = dataDirectory + "/" + year + "/" + month

        onlyfiles = [f for f in listdir(dir) if isfile(join(dir + "/" , f))]

        for file in onlyfiles:
            remove(dir + "/" + file)

        rmdir(dir)
    rmdir(dataDirectory + "/" + year)
rmdir(dataDirectory)

print("Done!")
