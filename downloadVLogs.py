#!/usr/bin/env python3
#
#  S3: Download Visitor Logs (should be used to download one month of logs)
#
import boto3
import S3TicketLib as s3f

# Parameters: s3 sessions, S3 source location, local destination location
# downloadVLogs ( s3_client, s3_resource, "gbads-aws-access-logs", "VisitorLogs/", "20230601", "20230615", "local_dir/" )

def downloadVLogs ( s3_client, s3_resource, bucket, prefix, first_date, last_date, local ):
    log_prefix = "VISITOR_LOGS_"

    response = s3_client.list_objects_v2( Bucket=bucket, Prefix=prefix )
    for content in response.get('Contents', []):
        # Remove the prefix from the Key
        x = len(prefix)
        filename = content['Key'][x:]
        if "/" not in filename:
            # Remove the log_prefix from the Key
            y = len(log_prefix)
            d1filename = filename[y:]
            # Get just the date part of the filename
            dfilename = d1filename[0:8]
            if dfilename >= first_date and dfilename <= last_date:
                dest = content['Key'].replace(prefix,local)
                ret = s3f.s3Download ( s3_resource, bucket, content['Key'], dest )
                if ( ret == -1 ):
                    return ( -1 )

    return ( 0 )

