import boto3


REGION_NAME = 'ap-southeast-2'
AMI_ID = 'ami-1a668878'  # Amazon Linux AMI 2017.09.1 (HVM), SSD Volume Type - ami-1a668878

ec2 = boto3.resource('ec2', region_name="ap-southeast-2")


# # create VPC
# vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
#
# # we can assign a name to vpc, or any resource, by using tag
# vpc.create_tags(Tags=[{"Key": "Pragya", "Value": "CreatedbyCode"}])
# vpc.wait_until_available()
#
# print(vpc.id)
#
#
# # Create sec group
# sec_group = ec2.create_security_group(
#     GroupName='slice_0', Description='slice_0 sec group', VpcId=vpc.id)
# sec_group.authorize_ingress(
#     CidrIp='0.0.0.0/0',
#     IpProtocol='TCP',
#     FromPort=0,
#     ToPort=65535
# )
# print(sec_group.id)

ec2 = boto3.client('ec2')
response = ec2.describe_key_pairs()


print (response)

print (response[1].KeyName)

