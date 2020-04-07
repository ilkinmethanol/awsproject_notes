# Imports.
import json
import datetime
import boto3
import decimal
from boto3.dynamodb.conditions import Key, Attr

# Dynamodb source from boto3.
dyndb = boto3.resource("dynamodb")

# Table dynamodb, which results will be stored.
device_events_table = dyndb.Table("saltreturn_updates")

# Custom decimal serializer.
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return int(obj)
    raise TypeError

# This method calculates percentage of successful packages.
def deployment_percentage_calc(stateTree):
    err_count,suc_count = error_successCounter(stateTree) 
    percentage = suc_count/(suc_count+err_count)
    return round(percentage*100)

# This method calculates number of failed and successed operations.     
def error_successCounter(stateTree):
    '''
    This method will grab stateTree and count false / true items . returns double value err_count and suc_count
    '''
    err_count = 0
    suc_count = 0
    for element in stateTree:
        if element["operation_result"] == "False":
            err_count = err_count+1
        else:
            suc_count = suc_count+1
    return err_count,suc_count

# Handles events which belongs to state.apply function and inserts them into table and returns operation response.
def create_state_apply_event(device_id, event_data):
    state_value = []
    for element,value in event_data["return"].items():
        # Making stateTree data
        state_value.append(
            {
                element:
                    {
                        "name": value["name"],
                        "changes": value["changes"],
                        "result": value["result"],
                        "comment": value["comment"],
                        "__sls__": value["__sls__"],
                        "__run_num__": value["__run_num__"],
                        "start_time": value["start_time"],
                        "duration": str(value["duration"]),
                        "__id__": value["__id__"]
                    },
                    "operation_result":str(value["result"]
                )
            }
        )

    device_id_value = event_data["id"]
    function_value = event_data["fun"]
    current_datetime = datetime.datetime.now()
    sort_key_value = "stateapply_"+current_datetime.strftime("%Y-%m-%d-%H:%M:%S")
    deployment_percentage_value = deployment_percentage_calc(state_value)

    if "description" in event_data:
        description_value = event_data["description"]
    else:
        description_value = " "
    
    # Checks, if percentage is equals 100 then deployment status is Ok, if equals 0 then deployment status is Fail, otherwise Partial.
    if float(deployment_percentage_value) == 100:
        deployment_status_value = "Ok"
    elif float(deployment_percentage_value) > 0 and float(deployment_percentage_value) < 100:
        deployment_status_value = "Partial"
    else:
        deployment_status_value = "Fail"
        
    # Counting failed and succeeded package results.
    err_count_value,suc_count_value = error_successCounter(state_value)
        
    # Insert operation.
    response = device_events_table.put_item(
        Item = {
            "device_id":device_id_value,
            "sort_key": sort_key_value,
            "deployment_percentage":deployment_percentage_value,
            "deployment_status":deployment_status_value,
            "failed":err_count_value,
            "function":function_value,
            "state":state_value,
            "succeeded":suc_count_value,
            "description":description_value
        }
    )
    return response,deployment_percentage_value,deployment_status_value
    
# Handles events which belongs to test.ping function and inserts them into table.
def create_test_ping_event(device_id,event_data):
    # Current date and time UTC.
    now_date = datetime.datetime.now()
    # Combine event tag and current UTC datetime.
    sort_key_value = "testping_"+now_date.strftime("%Y-%m-%d-%H:%M:%S")
    function_value = "test.ping"
    state_value = event_data
    
    # Fun data is not needed, thus we must pop it out from dict.
    del state_value["fun"]
    
    # Checking if event operated successfully, then we set _connectivity, _failed, _succeeded values.
    if event_data["success"]:
        connectivity_value = "Connected"
        failed_value = 0
        succeeded_value = 1
    else:
        connectivity_value = "Not connected"
        failed_value = 1
        succeeded_value = 0
    
    response = device_events_table.put_item(
        Item = {
            "device_id":device_id,
            "sort_key":sort_key_value,
            "failed":failed_value,
            "succeeded":succeeded_value,
            "function":function_value,
            "state":state_value,
            }
        )
    return response,connectivity_value

# Gets state.apply event and updates device_id status. 
def update_status_by_state_apply(device_id,deployment_percentage_value,deployment_status_value):
    # Current date and time UTC.
    now_date = datetime.datetime.now()
    
    # Update process of device status.
    response = device_events_table.update_item(
        Key={
            "device_id":device_id,
            "sort_key":"status"
        },
        UpdateExpression="SET datetime_lastseen=:datetime_lastseen, deployment_percentage=:deployment_percentage, deployment_status=:deployment_status, connectivity=:connectivity",
        ExpressionAttributeValues = {
            ":datetime_lastseen":str(now_date.strftime("%Y-%m-%d-%H:%M:%S")),
            ":deployment_percentage":deployment_percentage_value,
            ":deployment_status":deployment_status_value,
            ":connectivity":"Connected"
            },
            ReturnValues="UPDATED_NEW"
            )
    return response
    
# Gets state.apply event and pdates device_id status.
def update_status_by_test_ping(device_id,loaded_event,connectivity_value):
    # Current date and time UTC.
    now_date = datetime.datetime.now()
    
    # Update process of device status (changing datetime_lastseen and connectivity values).
    response = device_events_table.update_item(
        Key={
            "device_id":device_id,
            "sort_key":"status"
        },
        UpdateExpression="SET datetime_lastseen=:datetime_lastseen, connectivity=:connectivity",
        ExpressionAttributeValues = {
            ":datetime_lastseen":str(now_date.strftime("%Y-%m-%d-%H:%M:%S")),
            ":connectivity":connectivity_value
        },
        ReturnValues="UPDATED_NEW"
        )
    return response
    
# Checks missing keys from event data using keys list.
def check_missing_keys(device_event_data,important_keys_list):
    missing_keys = []
    
    # Iterating over important_keys_list and returns missing keys. 
    for key_name in important_keys_list:
        print("Checking keys...")
        if key_name in device_event_data:
            print(str(key_name)+" exists")
        else:
            missing_keys.append(key_name)
    return missing_keys

# Creating new device status, if there is no that kind of record with provided device_id.
def init_status(dev_id):
    return_init_device = ""
    try:
        
        # Get item from table for checking if it exists or not.
        get_item_with_id = device_events_table.get_item(
            Key={
                "device_id":dev_id,
                "sort_key":"status"
            }
            )
       
        # If it exists, just do nothing, prints item exists.
        if get_item_with_id:
            print("item_exists")
        else:
            # Otherwise creats new item with device_id.
            return_init_device = device_events_table.put_item(
                Item={"device_id":dev_id,"sort_key":"status"}
            )
    except Exception as e:
        raise e

    return return_init_device


def lambda_handler(event, context):

    if ('httpMethod' in event):

        # Checking if this method is for fetching the device events data:
        if event["httpMethod"] == "GET":

            # Device id, which is coming from with API path.
            device_id = event["pathParameters"]["deviceid"]

            all_device_events = device_events_table.scan(
                FilterExpression=Attr("device_id").eq(device_id) & Attr("sort_key").begins_with("testping") | Attr("sort_key").begins_with("stateapply_") 
                )

            if all_device_events["Items"]:
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                        },
                    "body": json.dumps({"Data":all_device_events["Items"]}, indent=4,default=decimal_default)
                }
            else:
                return {
                    "statusCode":404,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                        },
                    "body": json.dumps({"Error":"Events related to this id ("+str(device_id)+") are not available"},indent=4)
                }

        #  Checking if this method is for posting events.
        elif (event["httpMethod"] == "POST"):
            missing_keys = []
            device_event_data = event["body"]
            device_id = event['pathParameters']['deviceid']
            loaded_event = json.loads(device_event_data)

            # Checking if function is state.apply.
            if loaded_event["fun"] == "state.apply":

                # Required keys list for state_apply.
                important_keys_list_stateapply = ["success","return","retcode","jid","fun","fun_args","id"]

                # Checks missing keys from event data using keys list.
                missing_keys = check_missing_keys(device_event_data,important_keys_list_stateapply)

                # Check if there is(are) missing key(s) in list.      
                if len(missing_keys)>0:
                    return {
                        "statusCode":400,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                            },
                        "body": json.dumps({"message": "These keys ("+str(len(missing_keys))+") are missing in your post data: "+ str(missing_keys)}, indent=4)
                    }
                else:
                    try:
                        # Check if there is status for this item, if no, create a new one
                        init_status(device_id)

                        # Handles events which belongs to state.apply function and inserts them into table and returns operation response.
                        response,deployment_percentage_value,deployment_status_value = create_state_apply_event(device_id,loaded_event)

                        # Gets state.apply event and pdates device_id status. 
                        update_status = update_status_by_state_apply(device_id,deployment_percentage_value,deployment_status_value)

                    except Exception as e:
                        print(e)
                        # Raises exception and sends 500 error to user, if there are unexpected errors related with insertion of events.
                        return {
                            "statusCode":500,
                            "headers": {
                                "Content-Type": "application/json",
                                "Access-Control-Allow-Origin": "*"
                                },
                            "body": json.dumps({"Error":"Unexpected error occurred while inserting data, make sure you provided correct data."}, indent=4)
                        }
                    if (response):
                        # Sends success message to user with 200 statusCode.
                        print("Data_insertion_ok on device_id= ",device_id)
                        return {
                            "statusCode": 200,
                            "headers": {
                                "Content-Type": "application/json",
                                "Access-Control-Allow-Origin": "*"
                                },
                            "body": json.dumps({"message": "Successfully added event for "+str(device_id)}, indent=4)
                        }

            # Checking if function is test.ping.
            else:
                missing_keys = []
                device_event_data = event["body"]
                loaded_event = json.loads(device_event_data)

                if loaded_event["fun"] == "test.ping":
                    # Necessary keys for test.ping request. Test.ping response must include these keys.
                    important_keys_list_testping = ["success","return","retcode","jid","fun","fun_args","id"]

                    # Checks missing keys from event data using keys list.
                    missing_keys = check_missing_keys(device_event_data,important_keys_list_testping)

                # Check if there is(are) missing key(s) in list.     
                if len(missing_keys)>0:
                    return {
                        "statusCode":400,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                            },
                        "body": json.dumps({"message": "These keys ("+str(len(missing_keys))+") are missing in your post data: "+ str(missing_keys)}, indent=4)
                    }
                else:
                    try:
                        # Check if there is status for this item, if no, create a new one
                        init_status(device_id)

                        # Handles events which belongs to test.ping function and inserts them into table and returns operation response.
                        response,connectivity_value = create_test_ping_event(device_id,loaded_event)

                        # Gets state.apply event and updates device_id status.
                        update_status = update_status_by_test_ping(device_id,loaded_event,connectivity_value)

                    # Raises exception and sends 500 error to user, if there are unexpected errors related with insertion of events.   
                    except Exception as e:
                        print(e)
                        return {
                            "statusCode":500,
                            "headers": {
                                "Content-Type": "application/json",
                                "Access-Control-Allow-Origin": "*"
                                },
                            "body": json.dumps({"Error":"Unexpected error occurred while inserting data, make sure you provided correct data."}, indent=4)
                        }
                if (response):
                    print("Data_insertion_ok on device_id= ",device_id)
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                            },
                        "body": json.dumps({"message": "Successfully added event for "+str(device_id)}, indent=4)
                    }

    else:
        # Collect data from input body.
        device_id = event['deviceid']
        status_of_deployment = event['status']
        function_name = event['function']
        description_of_event = event['description']
        current_datetime = datetime.datetime.now()
        sort_key_value = "event_"+current_datetime.strftime("%Y-%m-%d-%H:%M:%S")

        # Check if there is status for this item, if no, create a new one.
        init_status(device_id)

        response = device_events_table.put_item(
        Item = {
            "device_id":device_id,
            "sort_key": sort_key_value,
            "deployment_status":status_of_deployment,
            "function":function_name,
            "description":description_of_event
        })

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
                },
            "body": json.dumps({"message":"Event saved to database."}, indent=4)
        }

