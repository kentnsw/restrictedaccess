# Restricted Access

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI.
The function removes any Security Group (SG) rule where the source is `0.0.0.0/0` and the port is 22 (ssh) periodically.
With customized parameters, it can evaluate any given ports. To opt out the remediation process, add a tag `'UnrestrictedAccess':'True'` to those security grouups.
After the evaluation and remediation, a report will send to the SNS topic. The report would look like

```json
{
  "date": "15/05/2021 05:16",
  "subject": "Restricted Access Evaluation and Remediation Report",
  "description": "To evaluate tcp/udp ports ['22', '3306'] against 0.0.0.0/0",
  "content": [
    "WARN: Security Group WebSg-132ZKNY6WR62H(sg-0223321c691) in VPC vpc-01317211a2 has an UnrestrictedAccess tag set as True.",
    "INFO: Revoked unrestricted access from Security Group testsg1(sg-09debfa0ddf1) in VPC vpc-43ec24. {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}",
    "INFO: Revoked unrestricted access from Security Group testsg2(sg-0cdacdb91017) in VPC vpc-43ec24. {'FromPort': 22, 'ToPort': 22, 'IpProtocol': 'tcp', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}",
    "INFO: Revoked unrestricted access from Security Group testsg2(sg-0cd70db91017) in VPC vpc-43ec24. {'FromPort': 3305, 'ToPort': 3307, 'IpProtocol': 'tcp', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}"
  ]
}
```

## Prerequisite
- An testing AWS account with appropriate privileges
- awscli, samcli

## Download and Tests

Clone the repository into your local environment.
Tests are defined in the `tests` folder. Use PIP to install the test dependencies and run tests.

```bash
cd tests
pip install -r requirements.txt --user
python -m pytest . -v
```

## Deploy the application

To build and deploy the application for the first time, run the following:

```bash
sam build
sam deploy --guided
```

Note:

- Make sure you have the permissions including create new IAM role, describe security groups, revoke ingress, create SNS topic and publish messages.
- `CAPABILITY_NAMED_IAM` is required while dploy. Change it to `capabilities = "CAPABILITY_NAMED_IAM"` in your `samconfig.toml`
- Subscribe to the new created SNS topic (`security_channel_restricted_access`) to see the remediation report
- It'd better set the stack name as `RestrictedSshAccessStack` for consitency
- Use the parameter overwrites for customization while deploying the stack, for example:

```bash
sam deploy --parameter-overrides "PortList='22,3306,3389'" "CronJobSchedule='cron(1/5 * * * ? *)'"
```

## Lambda function logs

The log is available in CloudWatch. alternatively, you can fetch it with the following:

```bash
sam logs -n RestrictedAccessFunc --stack-name RestrictedSshAccessStack --tail
```

Tips: You may login AWS Lambda console and perform a manual test rather than waiting for the scheduler.

## Cleanup

To delete the application, you can run the following:

```bash
aws cloudformation delete-stack --stack-name RestrictedSshAccessStack
```

