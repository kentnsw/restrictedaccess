from moto import mock_ec2, mock_sns
import boto3
import pytest
import restricted_access
import os
from faker import Faker


@pytest.fixture
def os_environ():
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:ap-southeast-2:123456789012:security_channel_restricted_ssh'
    os.environ['PORT_LIST'] = '22,3306'


@mock_ec2
def test_compliantSg(os_environ, ec2_client):
    result = restricted_access.evaluateSecurityGroups()
    assert result == []


@mock_ec2
def test_oneNoncompliantSg(ec2_client, ec2_resource, faker):
    gid = createSg(ec2_client, faker)
    sg = ec2_resource.SecurityGroup(gid)
    sg.load()

    # case 1: exactly the port
    authSgIngress(gid, 'tcp', 22, 22, [{'CidrIp': '0.0.0.0/0'}], ec2_client)
    result = restricted_access.evaluateSecurityGroups()
    assert result[0].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg.group_name}({gid})')
    sg.reload()
    assert len(sg.ip_permissions) == 0
    # after revoked
    result = restricted_access.evaluateSecurityGroups()
    assert result == []

    # case 2: port in range
    authSgIngress(gid, 'tcp', 20, 25, [{'CidrIp': '0.0.0.0/0'}], ec2_client)
    result = restricted_access.evaluateSecurityGroups()
    assert result[0].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg.group_name}({gid})')
    sg.reload()
    assert len(sg.ip_permissions) == 0


@mock_ec2
def test_oneNoncompliantSgWithMixedRanges(ec2_client, ec2_resource, faker):
    gid = createSg(ec2_client, faker)
    sg = ec2_resource.SecurityGroup(gid)
    sg.load()
    # case 3: noncompliant with compliant
    authSgIngress(gid, 'tcp', 22, 22, [{'CidrIp': '0.0.0.0/0'}], ec2_client)
    authSgIngress(gid, 'tcp', 22, 22, [{'CidrIp': '100.0.0.0/0'}], ec2_client)
    result = restricted_access.evaluateSecurityGroups()
    assert len(result) == 1
    assert result[0].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg.group_name}({gid})')
    sg.reload()
    assert sg.ip_permissions[0]['IpRanges'][0]['CidrIp'] == '100.0.0.0/0'

    # case 4: multi ports on top of case 3
    authSgIngress(gid, 'tcp', 20, 25, [{'CidrIp': '0.0.0.0/0'}], ec2_client)
    authSgIngress(gid, 'tcp', 3306, 3306, [
                  {'CidrIp': '0.0.0.0/0'}], ec2_client)
    result = restricted_access.evaluateSecurityGroups()
    assert len(result) == 2
    assert result[0].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg.group_name}({gid})')
    assert result[0].index("\'FromPort\': 20") > 0
    assert result[1].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg.group_name}({gid})')
    assert result[1].index("\'FromPort\': 3306") > 0
    sg.reload()
    assert sg.ip_permissions[0]['IpRanges'][0]['CidrIp'] == '100.0.0.0/0'


@mock_ec2
def test_multipleNoncompliantSgs(ec2_client, ec2_resource, faker):
    gid1 = createSg(ec2_client, faker)
    gid2 = createSg(ec2_client, faker)
    gid3 = createSg(ec2_client, faker)
    authSgIngress(gid1, 'tcp', 22, 22, [{'CidrIp': '0.0.0.0/0'}], ec2_client)
    authSgIngress(gid2, 'tcp', 3306, 3306, [
                  {'CidrIp': '0.0.0.0/0'}], ec2_client)
    authSgIngress(gid3, 'tcp', 3307, 3307, [
                  {'CidrIp': '200.0.0.0/0'}], ec2_client)
    sg1 = ec2_resource.SecurityGroup(gid1)
    sg1.load()
    sg2 = ec2_resource.SecurityGroup(gid2)
    sg2.load()

    result = restricted_access.evaluateSecurityGroups()
    assert len(result) == 2
    assert result[0].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg1.group_name}({gid1})')
    assert result[1].startswith(
        f'INFO: Revoked unrestricted access from Security Group {sg2.group_name}({gid2})')
    sg1.reload()
    sg2.reload()
    assert len(sg1.ip_permissions) == 0
    assert len(sg2.ip_permissions) == 0
    sg3 = ec2_resource.SecurityGroup(gid3)
    assert sg3.ip_permissions[0]['IpRanges'][0]['CidrIp'] == '200.0.0.0/0'


def createSg(ec2_client, faker):
    res = ec2_client.create_security_group(
        Description=faker.text(),
        GroupName=faker.name(),
    )
    return res['GroupId']


def authSgIngress(gid, protocal, fromPort, toPort, ipRanges, ec2_client):
    ec2_client.authorize_security_group_ingress(
        GroupId=gid,
        IpPermissions=[
            {
                'FromPort': fromPort,
                'IpProtocol': protocal,
                'IpRanges': ipRanges,
                'ToPort': toPort
            }
        ]
    )
