import json
import datetime
import boto3
from boto3.dynamodb.conditions import Key

# DynamoDB source.
dyndb = boto3.resource("dynamodb")

# DynamoDB table where metadata will be stored.
devicemetadata = dyndb.Table("devices_metadata")


# Declaration of function that writes metadata to db.
def write_metadata_to_db(device_id, device_meta):
    current_time = datetime.datetime.now()
    # Inserting metadata to table.
    response = devicemetadata.put_item(
        Item = {
            "deviceid": device_id,
            "datetime": current_time.strftime("%Y-%m-%d-%H:%M:%S"),
            "metadata": device_meta
            }
        )
    return response

def get_device_metadata(device_id):
    response = devicemetadata.query(
        KeyConditionExpression = Key("deviceid").eq(device_id)
    )
    del response["Items"][0]["deviceid"]
    return response

def lambda_handler(event, context):

    # If trigger is not http method, it means it's internal lambda call.
    if ('httpMethod' not in event):
        device_meta = event['metadata']
        device_id = event['deviceid']
    else:
        # If deviceid is not present in path parameters, return 400 and proper message. 
        if ('deviceid' not in event['pathParameters']):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                    },
                "body": json.dumps({"error":"Please provide deviceid as path parameters."}, indent=4)
            }

        # Get deviceid from path parameters.
        device_id = event["pathParameters"]["deviceid"]
    
    # Perform different actions basing on kind of request http method.
    if ('httpMethod' in event and event["httpMethod"] == "GET"):
        
        # Querying device metadata.
        device_metadata = get_device_metadata(device_id)
                    
        # Check if data contains Items.
        if device_metadata["Items"]:
            
            # Returning success message to user.
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                    },
                "body": json.dumps({"message":device_metadata["Items"][0]}, indent=4)
            }
        else:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                    },
                "body": json.dumps({"Error": f"There's no metadata for device {device_id}."},indent=4)
            }
    
    elif (('httpMethod' in event and event["httpMethod"] == "POST") or 'httpMethod' not in event):
        if ('httpMethod' in event):
            # Load request body to dict.
            body_dict = json.loads(event["body"])
            device_meta = body_dict["metadata"]
        
        try:
            # Insert metadata to database.
            response = write_metadata_to_db(device_id, device_meta)
        except Exception as e:
            print(e)
            # Raises exception and sends 500 error to user, if there are unexpected errors related to insertion of metadata.
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                    },
                "body": json.dumps({"Error":"Unexpected error occurred while inserting data, make sure you provided correct body that contains \'deviceid\' and \'metadata\' parameters." }, indent=4)
            }
        
        # Return success message and status code.
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"message":f"Metadata for device {device_id} has been added successfully."})
            }
    
    # If any other method than POST or GET.
    else:
        return {
            "statusCode": 403,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                    },
            "body": json.dumps({"error":"This method is not allowed."}, indent=4)
        }