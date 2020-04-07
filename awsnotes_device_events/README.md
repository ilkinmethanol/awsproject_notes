# **devices-deviceid-events**

![](images_documentation/devices-deviceid-events.png)


### **POST:**

**Description:** Insert event for specific device to dynamodb.

>  ##### **URL:** `https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/events`
>
>  ##### **CURL:** `curl --header "Content-Type: application/json" --request POST --data '{"deviceid": "e8613951-216a-4ad7-85e3-dd963d0823c4", "status": "Failed", "description": "testdescription", "function": "get-greengrass-configurations"}' https://deviceregistry.mccs.internal.delaval.cloud/devices`
>
>  ##### **Example JSON-formatted body:**
>
>  - Function takes different inputs, it's configured to be called from different places. Below you can find an example body used to add 'failed' event from within 'get-greengrass-configurations' lambda.
>
>  ```
>  {
>  	"deviceid": "e8613951-216a-4ad7-85e3-dd963d0823c4", 
>  	"status": "Failed",
>  	"description": "test description",
>  	"function": "get-greengrass-configurations"
>  }
>  ```
>
>  ##### **Return format:**
>
>  ```
>  {
>  	"message": "Successfully added events for e8613951-216a-4ad7-85e3-dd963d0823c4"
>  }
>  ```
>


### **GET:**

**Description:** Get events for given device from database.

> ##### **URL:** `https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/events`
>
> ##### **CURL:**  `curl https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/events`
>
> 
>
> ##### **Return format:**
>
> ```
> [
>         {
>             "succeeded": 1,
>             "sort_key": "event_2020-03-24-14:27:15",
>             "device_id": "9b7b47da-9a12-4623-b7cf-e2410af34022",
>             "failed": 0,
>             "function": "test.ping",
>             "state": {
>                 "fun_args": [
>                     "string"
>                 ],
>                 "jid": "asdasdas",
>                 "success": true,
>                 "return": {
>                     "name": {
>                         "duration": 0,
>                         "result": true,
>                         "start_time": "sdsdsd",
>                         "__id__": "sdsdadasdasda",
>                         "__run_num__": 0,
>                         "changes": {},
>                         "name": "asdas",
>                         "__sls__": "sdsdsds",
>                         "comment": "sdsdsd"
>                     }
>                 },
>                 "retcode": 0
>             }
>         },
>         {
>             "sort_key": "event_2020-03-25-16:43:34",
>             "device_id": "9b7b47da-9a12-4623-b7cf-e2410af34022",
>             "function": "get-greengrass-configuration",
>             "deployment_status": "Failed",
>             "description": "Group b76f3827-f211-4710-87db-2a0f7021fcc5 won't be pushed, because pkg_spiderman_gwip which is required in config JSON is missing in core thing attributes."
>         }
> ]
> ```

