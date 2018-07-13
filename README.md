# webhooks-rt-forwarder
A simple python-3 GitHub issue forwarder to [Best Practical Request Tracker](https://bestpractical.com/request-tracker/) via webhooks.

## Requirements

Uses the following:
* AWS Lambda
* AWS API Gateway
* AWS DynamoDB (for issue # to ticket # mapping)
* [python-rt](https://github.com/CZ-NIC/python-rt)

NOTE: this assumes `create_ticket()` in python-rt supports the `files` parameter for creating tickets with attachments.

## Lambda deployment

To generate `upload.zip`: run `make`.

## Environment variables
| Name              | Value                                         |
|-------------------|-----------------------------------------------|
| `RT_REST_BASEURL` | URL to RT REST endpoint                       |
| `RT_USER`         | RT username                                   |
| `RT_PASS`         | RT password                                   |
| `RT_QUEUE`        | Queue for the ticket                          |
| `RT_REQUESTOR`    | Requestor username or email                   |
| `GH_SECRET`       | Webhook secret                                |
| `DYN_TABLE`       | DynamoDB table name                           |
| `RT_CA_CERT`      | _optional_ CA bundle for HTTPS                |
| `DEBUG`           | _optional_ If present, produces lots of noise |
