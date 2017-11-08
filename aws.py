#!/usr/bin/env python

import boto3
import time

REGION_NAME = 'ap-southeast-2'
AMI_ID = 'ami-aa1b34cf'  # Amazon Linux AMI 2017.09.1 (HVM), SSD Volume Type

client = boto3.client('ec2')

# Create a VPC  -
vpc = client.create_vpc(
    CidrBlock='10.0.0.0/16'
)

print (vpc)






