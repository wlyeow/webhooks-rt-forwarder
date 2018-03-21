# webhooks-rt-forwarder
A python-3.6 simple forwarder for github issues to [Best Practical Request Tracker](https://bestpractical.com/request-tracker/) via webhooks.

Uses the following:
* AWS Lambda
* AWS API Gateway
* AWS DynamoDB (for issue # to ticket # mapping)
* [python-rt](https://github.com/CZ-NIC/python-rt)

NOTE: this assumes `create_ticket()` in [python-rt](https://github.com/wlyeow/python-rt) supports the `files` parameter for creating tickets with attachments.

To generate `upload.zip`: run `make`.
