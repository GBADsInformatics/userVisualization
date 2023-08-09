#!/usr/bin/env python3
import newS3TicketLib as ticket

access, secret = ticket.get_keys()
s3_resource = ticket.credentials_resource ( access, secret )

# for download
bucket = "gbads-aws-access-logs"
source = "AccessLogs/ACCESS_LOGS_20230505.csv"    # must have full path name 
destination_path = "localfile.csv"                # puts file in local . directory with given name

ret = ticket.s3Download ( s3_resource, bucket, source, destination_path )
print ( "download ret = "+str(ret) )

# for upload
bucket = "gbads-comments"
source_path = "localfile.csv"
destination_path = "underreview/testfile.csv"
ret = ticket.s3Upload ( s3_resource, bucket, source_path, destination_path )
print ( "upload ret = "+str(ret) )

