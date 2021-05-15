import sys
import os
import boto3
import pytest
from moto import mock_ec2, mock_sns

here = os.path.abspath("../functions")
sys.path.insert(0, here)


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def ec2_client(aws_credentials):
    with mock_ec2():
        ec2c = boto3.client('ec2')
        yield ec2c


@pytest.fixture
def ec2_resource(aws_credentials):
    with mock_ec2():
        ec2r = boto3.resource('ec2')
        yield ec2r


@pytest.fixture
def sns_client(aws_credentials):
    with mock_sns():
        snsc = boto3.client('sns')
        yield snsc
