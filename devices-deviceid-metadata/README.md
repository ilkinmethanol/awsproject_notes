# devices-deviceid-metadata

Lambda handles POST and GET operations on metadata for devices. Lambda function is pinned to two endpoints - different actions are performed basing on kind of http method of request.

### **POST:**

**Description:** Adds metadata for specific device to dynamodb table.

>  ##### **URL:** `https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/metadata`
>
>  ##### **CURL:** `curl --header "Content-Type: application/json" --request POST --data '{"metadata": "somemetadata"}' https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/metadata`
>
>  ##### **Example JSON-formatted body:**
>
>  ```
>  {
>  	"metadata": "somemetadata"
>  }
>  ```
>
>  ##### **Return format:**
>
>  ```
>  {
>  	"message": "Metadata for device {device_id} has been added successfully."
>  }
>  ```
>


### **GET:**

**Description:** Gets metadata for particular device.

> ##### **URL:** `https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/metadata`
>
> ##### **CURL:** `curl https://deviceregistry.mccs.internal.delaval.cloud/devices/{deviceid}/metadata`
>
> ##### **Return format:**
>
> ```
> {
> 	"deviceid": "value",
> 	"datetime": "value",
> 	"metadata": "value"
> }
> ```
