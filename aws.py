#!/usr/bin/env python

import boto3


REGION_NAME = 'ap-southeast-2'
AMI_ID = 'ami-1a668878'  # Amazon Linux AMI 2017.09.1 (HVM), SSD Volume Type - ami-1a668878

ec2 = boto3.resource('ec2', region_name="ap-southeast-2")

# create VPC
vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')

# we can assign a name to vpc, or any resource, by using tag
vpc.create_tags(Tags=[{"Key": "Pragya", "Value": "CreatedbyCode"}])
vpc.wait_until_available()

print(vpc.id)


# create subnet 1 - Public
subnet1 = ec2.create_subnet(
    AvailabilityZone='ap-southeast-2a',
    CidrBlock='10.0.1.0/24',
    VpcId=vpc.id,)

print(subnet1.id)

# create subnet 2  - Private
subnet2 = ec2.create_subnet(
    AvailabilityZone='ap-southeast-2b',
    CidrBlock='10.0.2.0/24',
    VpcId=vpc.id,)

print(subnet2.id)


# create then attach internet gateway
ig = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=ig.id)
print(ig.id)

# create a route table and a public route
route_table = vpc.create_route_table()
route = route_table.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=ig.id
)
print(route_table.id)


# associate the route table with the subnet 1 to make it public
route_table.associate_with_subnet(SubnetId=subnet1.id)

# Create sec group
sec_group = ec2.create_security_group(
    GroupName='slice_0', Description='slice_0 sec group', VpcId=vpc.id)
sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='TCP',
    FromPort=0,
    ToPort=65535
)

print(sec_group.id)

# find image id ami-aa1b34cf/ ap-souteast2
# Create instance
instances = ec2.create_instances(
    ImageId=AMI_ID, InstanceType='t2.micro', MaxCount=1, MinCount=1,
    NetworkInterfaces=[{'SubnetId': subnet1.id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True,
                        'Groups': [sec_group.group_id]}])

instances[0].wait_until_running()

print(instances[0].id)