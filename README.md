# Restricted Access

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI.
The function removes any Security Group (SG) rule where the source is 0.0.0.0/0 and the port is 22 (ssh) periodically. With customized parameters, it can evaluate any given ports.

## Download and Tests

Clone the repository into your local environment.
Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

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

- make sure you have the permissions including create new IAM role, describe security groups, revoke ingress, create SNS topic and publish messages.
- CAPABILITY_NAMED_IAM is required
- It'd better set the stack name as RestrictedSshAccessStack for consitency
- Use the parameter overwrites for customization while deploying the stack, for example:

```bash
sam deploy --parameter-overrides "PortList='22,3306,3389'" "CronJobSchedule='cron(1/5 * * * ? *)'"
```

## Lambda function logs

The log is available in CloudWatch. alternatively, you can fetch it with the following:

```bash
sam logs -n RestrictedAccessFunc --stack-name RestrictedSshAccessStack --tail
```

## Cleanup

To delete the application, you can run the following:

```bash
aws cloudformation delete-stack --stack-name RestrictedSshAccessStack
```
