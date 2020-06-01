import boto3
import json
import time
import configparser
import pandas as pd

# AWS config parameters
KEY = None
SECRET = None

DWH_CLUSTER_TYPE = None
DWH_NUM_NODES = None
DWH_NODE_TYPE = None

DWH_CLUSTER_IDENTIFIER = None
DWH_DB = None
DWH_DB_USER = None
DWH_DB_PASSWORD = None
DWH_PORT = None

DWH_IAM_ROLE_NAME = None


def config_parser():
    """
    Set the AWS Config parameters with value from dwh.cfg config file
    """

    global KEY, SECRET, DWH_CLUSTER_TYPE, DWH_NUM_NODES
    global DWH_NODE_TYPE, DWH_CLUSTER_IDENTIFIER, DWH_DB
    global DWH_DB_USER, DWH_DB_PASSWORD, DWH_PORT, DWH_IAM_ROLE_NAME

    print("Parsing the configuration file...\n")

    config = configparser.ConfigParser()
    with open('dwh.cfg') as configfile:
        config.read_file(configfile)

        KEY = config.get('AWS', 'KEY')
        SECRET = config.get('AWS', 'SECRET')

        DWH_CLUSTER_TYPE = config.get("DWH", "DWH_CLUSTER_TYPE")
        DWH_NUM_NODES = config.get("DWH", "DWH_NUM_NODES")
        DWH_NODE_TYPE = config.get("DWH", "DWH_NODE_TYPE")

        DWH_IAM_ROLE_NAME = config.get("DWH", "DWH_IAM_ROLE_NAME")
        DWH_CLUSTER_IDENTIFIER = config.get("DWH", "DWH_CLUSTER_IDENTIFIER")

        DWH_DB = config.get("CLUSTER", "DB_NAME")
        DWH_DB_USER = config.get("CLUSTER", "DB_USER")
        DWH_DB_PASSWORD = config.get("CLUSTER", "DB_PASSWORD")
        DWH_PORT = config.get("CLUSTER", "DB_PORT")


def aws_client(service, region):
    """
    Creates an AWS client (specified by the argument) in region (specified by argument)
    :param service: The service to be created
    :param region: The region where service has to be created
    :return client: The client for AWS service
    """

    global KEY, SECRET
    client = boto3.client(service, aws_access_key_id=KEY, aws_secret_access_key=SECRET, region_name=region)

    return client


def aws_resource(name, region):
    """
    Creates an AWS resource (specified by the argument) in region (specified by argument)
    :param name: The resource to be created
    :param region: The region where resource has to be created
    :return resource: The resource for AWS service
    """

    global KEY, SECRET
    resource = boto3.resource(name, region_name=region, aws_access_key_id=KEY, aws_secret_access_key=SECRET)

    return resource


def iam_create_role(iam):
    """
    Create the AWS Identity and Access Management (IAM) role. Attach AmazonS3ReadOnlyAccess role policy to the IAM
    specified in argument. Return the IAM role ARN string
    :param iam: Boto3 client for IAM
    :return roleArn: IAM role ARN string
    """

    global DWH_IAM_ROLE_NAME

    dwhRole = None
    try:
        print('1.1 Creating a new IAM Role')
        dwhRole = iam.create_role(
            Path='/',
            RoleName=DWH_IAM_ROLE_NAME,
            Description="Allows Redshift clusters to call AWS services on your behalf.",
            AssumeRolePolicyDocument=json.dumps(
                {'Statement': [{'Action': 'sts:AssumeRole',
                                'Effect': 'Allow',
                                'Principal': {'Service': 'redshift.amazonaws.com'}}],
                 'Version': '2012-10-17'})
        )
    except Exception as exep:
        print(exep)
        dwhRole = iam.get_role(RoleName=DWH_IAM_ROLE_NAME)

    print('1.2 Attaching Policy')
    dwhRole_policy = iam.attach_role_policy(RoleName=DWH_IAM_ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy"
                                                                                  "/AmazonS3ReadOnlyAccess")[
                                            'ResponseMetadata']['HTTPStatusCode']

    roleArn = iam.get_role(RoleName=DWH_IAM_ROLE_NAME)['Role']['Arn']

    return roleArn


def init_cluster_creation(redshift, roleArn):
    """
    Initiate the AWS Redshift cluster creation process
    :param redshift: Boto3 client for the Redshift
    :param roleArn: The ARN string for IAM role
    :return boolean:
    """

    global DWH_CLUSTER_TYPE, DWH_NODE_TYPE, DWH_NUM_NODES
    global DWH_DB, DWH_CLUSTER_IDENTIFIER, DWH_DB_USER, DWH_DB_PASSWORD

    print("2. Starting Redshift cluster creation")
    try:
        response = redshift.create_cluster(
            ClusterType=DWH_CLUSTER_TYPE,
            NodeType=DWH_NODE_TYPE,
            NumberOfNodes=int(DWH_NUM_NODES),

            DBName=DWH_DB,
            ClusterIdentifier=DWH_CLUSTER_IDENTIFIER,
            MasterUsername=DWH_DB_USER,
            MasterUserPassword=DWH_DB_PASSWORD,

            IamRoles=[roleArn]
        )

        print("Redshift cluster creation http response status code: ")
        print(response['ResponseMetadata']['HTTPStatusCode'])
        return response['ResponseMetadata']['HTTPStatusCode'] == 200

    except Exception as exep:
        print(exep)
        return False


def config_update_cluster(redshift):
    """
    Write the cluster endpoint and IAM ARN string to the dwh.cfg configuration file
    :param redshift: Boto3 client for Redshift
    """

    global DWH_CLUSTER_IDENTIFIER

    print("Writing the cluster endpoint address and IAM Role ARN to the config file...\n")
    cluster_props = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]

    config = configparser.ConfigParser()
    with open('dwh.cfg') as configfile:
        config.read_file(configfile)

    config.set("CLUSTER", "HOST", cluster_props['Endpoint']['Address'])
    config.set("IAM_ROLE", "ARN", cluster_props['IamRoles'][0]['IamRoleArn'])

    with open('dwh.cfg', 'w+') as configfile:
        config.write(configfile)

    config_parser()


def redshift_cluster_status(redshift):
    """
    Retrieves the Redshift cluster status
    :param redshift: Boto3 client for Redshift
    :return cluster_status: The cluster status
    """

    global DWH_CLUSTER_IDENTIFIER

    cluster_props = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]
    cluster_status = cluster_props['ClusterStatus'].lower()

    return cluster_status


def aws_open_redshift_port(ec2, redshift):
    """
    Opens an incoming TCP port to access Redshift cluster endpoint on VPC security group
    :param ec2: Boto3 client for EC2 instance
    :param Redshift: Boto3 client for Redshift
    """

    global DWH_CLUSTER_IDENTIFIER, DWH_PORT
    cluster_props = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]

    try:
        vpc = ec2.Vpc(id=cluster_props['VpcId'])
        all_security_groups = list(vpc.security_groups.all())
        print(all_security_groups)
        defaultSg = all_security_groups[0]
        print(defaultSg)

        defaultSg.authorize_ingress(
            GroupName=defaultSg.group_name,
            CidrIp='0.0.0.0/0',
            IpProtocol='TCP',
            FromPort=int(DWH_PORT),
            ToPort=int(DWH_PORT)
        )
    except Exception as exep:
        print(exep)


def main():
    config_parser()

    ec2 = aws_resource('ec2', "us-west-2")
    s3 = aws_resource('s3', "us-west-2")
    iam = aws_client('iam', "us-west-2")
    redshift = aws_client('redshift', "us-west-2")

    roleArn = iam_create_role(iam)

    clusterCreationStarted = init_cluster_creation(redshift, roleArn)

    if clusterCreationStarted:
        print("The cluster is being created.")

        while True:
            print("Checking if the cluster is created...")

            if redshift_cluster_status(redshift) == 'available':
                config_update_cluster(redshift)
                aws_open_redshift_port(ec2, redshift)
                break
            else:
                print("Cluster is still being created. Please wait.")

            time.sleep(30)
        print("Cluster creation successful.\n")
        

if __name__ == '__main__':
    main()
