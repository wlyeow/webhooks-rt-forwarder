# webhooks-rt-forwarder
A python-3.6 simple forwarder for github issues to [Best Practical Request Tracker](https://bestpractical.com/request-tracker/) via webhooks.

Uses the following:
* AWS Lambda
* AWS API Gateway
* AWS DynamoDB (for issue # to ticket # mapping)
* [python-rt](https://github.com/CZ-NIC/python-rt)
