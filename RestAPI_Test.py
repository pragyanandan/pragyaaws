
import flask
from flask import request

app = flask.Flask(__name__)
app.config["DEBUG"] = True
import json

import os

SL = 200
SW = 300
SH = 150
ML = 300
MW = 400
MH = 200
LL = 400
LW = 600
LH = 250
allowed_weight = 25
scost = 5.0
mcost = 7.5
lcost = 8.5



def return_package_cost(Package_length, Package_Width, Package_Height, Package_Weight) :
    if Package_Weight > allowed_weight:
        x = {
            "PackageSize": "Not Applicable",
            "PackageCost": "Not Applicable",
            "ErrorMessage": "Weight exceed than the allowed amount"
        }
        y = json.dumps(x)
        return y
    else :
        if (Package_length <= SL) and (Package_Width <= SW) and (Package_Height <= SH):
            x = {
                "PackageSize": "Small",
                "PackageCost": scost
            }
            y = json.dumps(x)
            return y
        elif (Package_length <= ML) and (Package_Width <= MW) and (Package_Height <= MH):
            x = {
                "PackageSize": "Medium",
                "PackageCost": mcost
            }
            y = json.dumps(x)
            return y
        elif (Package_length <= LL) and (Package_Width <= LW) and (Package_Height <= LH):
            x = {
                "PackageSize": "Large",
                "PackageCost": lcost
            }
            y = json.dumps(x)
            return y
        else:
            x = {
                "PackageSize": "Not Applicable",
                "PackageCost": "Not Applicable",
                "ErrorMessage": "Dimensions exceed the alloed limits"
            }
            y = json.dumps(x)
            return y

## To return the Package Size and Cost
## Way of calling API
## http://127.0.0.1:5000/api/v1/resources/packagesize?package_length=200&package_width=400&package_height=150&package_weight=22
@app.route('/api/v1/resources/packagesize', methods=['GET'])
def PackageSizeCost():
    # Check if a package_length was provided as part of the URL.
    package_length = 0

    if 'package_length' in request.args:
        package_length = int(request.args['package_length'])
    else:
        return "Error: No package_length field provided. Please specify a package_length."

    if 'package_width' in request.args:
        package_width = int(request.args['package_width'])
    else:
        return "Error: No package_width field provided. Please specify a package_width."

    if 'package_height' in request.args:
        package_height = int(request.args['package_height'])
    else:
        return "Error: No package_height field provided. Please specify a package_height."

    if 'package_weight' in request.args:
        package_weight = int(request.args['package_weight'])
    else:
        return "Error: No package_weight field provided. Please specify a package_weight."


    return return_package_cost(package_length, package_width, package_height, package_weight)


## Way of calling API - API for launching Auto Task
## http://127.0.0.1:5000/api/v1/resources/robot/tango
@app.route('/api/v1/resources/robot/tango', methods=['GET'])
def Tango():
    os.system("C:\Tango.bat")
    x = {
        "Tango Success": "Yes",
        "Error Code": "None"
    }
    y = json.dumps(x)
    return y

## Way of calling API  - This API is for creating financial Sheet
## http://127.0.0.1:5000/api/v1/resources/robot/tango
@app.route('/api/v1/resources/robot/jarvis', methods=['GET'])
def Jarvis():
    os.system("C:\Jarvis.bat")
    x = {
        "Jarvis Success": "Yes",
        "Error Code": "None"
    }
    y = json.dumps(x)
    return y

## Way of calling API  - This API is for creating Contract and Project
## http://127.0.0.1:5000/api/v1/resources/robot/tango
@app.route('/api/v1/resources/robot/spider', methods=['GET'])
def spider():
    os.system("C:\spider.bat")
    x = {
        "Spider Success": "Yes",
        "Error Code": "None"
    }
    y = json.dumps(x)
    return y

app.run()

#This is the code for API
