
import requests
import json

print ("pragya")


url = "http://api.fixer.io/latest?symbols=NZD,INR"

response = requests.get(url)

print (response)

data = response.text

print (data)

parsed = json.loads(data)

print (parsed)
