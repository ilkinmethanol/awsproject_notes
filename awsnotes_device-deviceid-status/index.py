# Imports.
import json
import datetime
import boto3
import decimal

# Dynamodb source from boto3.
dyndb = boto3.resource("dynamodb")

# DynamoDB table where results are stored.
device_events_table = dyndb.Table("saltreturn_updates")

# Custom decimal serializer.
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return int(obj)
    raise TypeError

def lambda_handler(event, context):

    # Check if lambda was called internally or using http request.
    # Get device_id.
    if ('httpMethod' in event):
        
        # Get device id from API event.
        device_id = event["pathParameters"]["device_id"]
    else:
        device_id = event['device_id']

    # Get device status data using device_id.  
    device_status = device_events_table.get_item(
        Key={
            "device_id": device_id,
            "sort_key": "status"
        }
    )
    
    # Make sure device_status item contains "Item" property. 
    if "Item" in device_status:
        return {
            "headers":{
                    "Content-Type":"application/json","Access-Control-Allow-Origin": "*"
                },
            "statusCode": 200,
            "body": json.dumps({"Data": device_status["Item"]}, indent=4, default=decimal_default)
        }
    # If it doesn't, return Not Found and proper message. 
    else:
        return {
            "headers":{
                    "Content-Type":"application/json","Access-Control-Allow-Origin": "*"
                },
            "statusCode": 404,
            "body" : json.dumps({"Error": f"No status found for device {device_id}."}, indent=4)
        }
