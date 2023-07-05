from os import listdir, remove
from os.path import isfile, join

print("Cleaning...")
dataDirectory = "VisitorLogs/"

onlyDirs = [f for f in listdir(dataDirectory )]
for dir in onlyDirs:
    onlyfiles = [f for f in listdir(dataDirectory + dir + "/") if isfile(join(dataDirectory + dir + "/" , f))]

    for file in onlyfiles:
        remove(dataDirectory + dir + "/" + file)

print("Done!")
