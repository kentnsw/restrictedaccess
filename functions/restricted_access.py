import os
import boto3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    report = {}
    report['date'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    report['subject'] = f'Restricted Access Evaluation and Remediation Report'
    report['description'] = f"To evaluate tcp/udp ports {os.environ['PORT_LIST'].split(',')} against 0.0.0.0/0"
    logger.info(report['subject'])
    logger.info(report['description'])


    try:
        report['content'] = evaluateSecurityGroups()
    except Exception as e:
        report['error'] = str(e)
    finally:
        sendSnsReport(report)

    return report


def evaluateSecurityGroups():
    content = []
    EC2_CLIENT = boto3.client('ec2')
    EC2_RESOURSE = boto3.resource('ec2')

    try:
        # NOTE: moto_ec2 hasn't supported ip-permission.cidr fileter
        # sgs = EC2_CLIENT.describe_security_groups(Filters=[
        #     {
        #         'Name': 'ip-permission.cidr',
        #         'Values': ['0.0.0.0/0']
        #     }
        # ])
        sgs = EC2_CLIENT.describe_security_groups()
        logger.info(f"Loaded {len(sgs['SecurityGroups'])} Security Groups")
        
        for sgStr in sgs['SecurityGroups']:
            sg = SecurityGroup(sgStr)
            unrestrictedTag = sg.getTagValue('UnrestrictedAccess')
            if unrestrictedTag and unrestrictedTag.lower() == 'true':
                msg = f'WARN: Security Group {sg.name}({sg.id}) in VPC {sg.vpcId} has an UnrestrictedAccess tag set as True.'
                logger.warning(msg)
                content.append(msg)
                continue
            for ipPerm in sg.ipPermissions:
                # NOTE: this is a hard code env name in CF template for quick deploy
                for port in os.environ['PORT_LIST'].split(','):
                    delIpPerm = ipPerm.findIpv4Permission(
                        int(port), 'tcp|udp', '0.0.0.0/0')
                    if delIpPerm:
                        tmp = revokeIngress(EC2_RESOURSE, sg, delIpPerm)
                        if tmp:
                            content.append(tmp)
                        break
        return content
    except Exception as e:
        msg = 'Failed to evaluate unrestricted access. '
        logger.exception(msg)
        raise Exception(msg)


def revokeIngress(EC2_RESOURSE, sg, delIpPerm):
    if not delIpPerm:
        return None

    sgInstance = EC2_RESOURSE.SecurityGroup(sg.id)
    res = sgInstance.revoke_ingress(IpPermissions=[delIpPerm])

    msg = f' from Security Group {sg.name}({sg.id}) in VPC {sg.vpcId}. {delIpPerm}'
    if res['ResponseMetadata']['HTTPStatusCode'] == 200:
        msg = f'INFO: Revoked unrestricted access' + msg
        logger.info(msg)
    else:
        msg = f'ERROR: Failed to revoke unrestricted access' + msg
        logger.error(msg)

    return msg


def sendSnsReport(report):
    SNS_CLIENT = boto3.client('sns')

    # NOTE: this is a hard code env name in CF template for quick deploy
    SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
    try:
        res = SNS_CLIENT.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=str(report),
            Subject=report['subject']
        )
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info(f'Sent report to SNS topic {SNS_TOPIC_ARN}. MessageId {res["MessageId"]}')
        else:
            raise Exception(res)
    except Exception as e:
        logger.error(f'Failed to send report to topic {SNS_TOPIC_ARN} with message:')
        logger.error(report)
        logger.error(e)


class IpPermission:
    def __init__(self, ipPerm) -> None:
        self.fromPort = ipPerm['FromPort'] if 'FromPort' in ipPerm else -1
        self.toPort = ipPerm['ToPort'] if 'ToPort' in ipPerm else -1
        self.ipProtocol = ipPerm['IpProtocol']
        self.ipRanges = ipPerm['IpRanges']

    def findIpv4Permission(self, port, protocal='tcp|udp', fromIpRange='0.0.0.0/0'):
        if self.fromPort <= port and self.toPort >= port and self.ipProtocol in protocal or self.ipProtocol == '-1':
            irs = [ir for ir in self.ipRanges if ir['CidrIp'] == fromIpRange]
            if len(irs):
                perm = {
                    'FromPort': self.fromPort,
                    'ToPort': self.toPort,
                    'IpProtocol': self.ipProtocol,
                    'IpRanges': irs
                }
                if self.fromPort == -1:
                    perm.pop('FromPort')
                if self.toPort == -1:
                    perm.pop('ToPort')
                return perm
        return None


class SecurityGroup:

    def __init__(self, sg) -> None:
        self.id = sg['GroupId']
        self.name = sg['GroupName']
        self.vpcId = sg['VpcId'] if 'VpcId' in sg else None
        self.tags = sg['Tags'] if 'Tags' in sg else None
        self.ipPermissions = [IpPermission(perm)
                              for perm in sg['IpPermissions']]
        self.sg = sg

    def getTagValue(self, key):
        if not self.tags:
            return None

        for tag in self.tags:
            if key == tag['Key']:
                return tag['Value']
        return None


if __name__ == "__main__":
    class Context:
        pass

    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:ap-southeast-2:065125734684:security_channel_restricted_access'
    os.environ['PORT_LIST'] = '22,3306'
    print(lambda_handler({}, Context()))
