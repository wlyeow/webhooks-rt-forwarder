#!/usr/bin/env python3

import os
import rt
import hashlib
import hmac

import boto3
import io

import json
from collections import namedtuple

_RT_BASEURL = os.environ['RT_REST_BASEURL']
_RT_USER = os.environ['RT_USER']
_RT_PASS = os.environ['RT_PASS']
_RT_QUEUE = os.environ['RT_QUEUE']
_RT_REQUESTOR = os.environ['RT_REQUESTOR']
_RT_CA_CERT = os.environ.get('RT_CA_CERT', True)

_GITHUB_SECRET = os.environ['GH_SECRET'].encode()

_DYNAMO_TABLE = os.environ['DYN_TABLE']

_DEBUG = 'DEBUG' in os.environ

#preloads
dynamo = boto3.client('dynamodb')

if _DEBUG:
    import sys
    import traceback
    import pprint

class Tracker:
    def __init__(self):
        self.tracker = rt.Rt(
                _RT_BASEURL, _RT_USER, _RT_PASS,
                default_queue= _RT_QUEUE,
                verify_cert=_RT_CA_CERT)

        if _DEBUG:
            print('Logging into RT.')

        if not self.tracker.login():
            raise ConnectionError('Incorrect username or password')

        if _DEBUG:
            print('Succeeded.')

    def createTicket(self, **kwargs):
        return self.tracker.create_ticket(**kwargs)

    def replyTicket(self, ticket_id, **kwargs):
        return self.tracker.reply(ticket_id, **kwargs)

    def resolveTicket(self, ticket_id):
        return self.tracker.edit_ticket(ticket_id, Status='resolved')

    def __del__(self):
        self.tracker.logout()

def storeTicketNumber(repo_name, issue_id, ticket_id):
    dynamo.put_item(TableName= _DYNAMO_TABLE,
            Item= { 'Repo': {'S':repo_name}, 'IssueId': {'N':str(issue_id)}, 'TicketId': {'S':str(ticket_id)} })

def getTicketNumber(repo_name, issue_id):
    item = dynamo.get_item(TableName= _DYNAMO_TABLE,
            Key={ 'Repo': {'S':repo_name}, 'IssueId': {'N':str(issue_id)} })['Item']

    if _DEBUG:
        print('item retrieved:')
        pprint.pprint(item)
    
    return int(item['TicketId']['S'])

def getEventDetails(event):
    _X_SIG = 'X-Hub-Signature'
    _X_EVENT = 'X-GitHub-Event'

    _X_EVENT_TYPE = set(['issues', 'issue_comment'])

    if event['headers'][_X_EVENT] not in _X_EVENT_TYPE:
        raise KeyError(f'GitHub event type "{event[_X_EVENT]}" is not valid')

    ( hash_algo, hash_value ) = event['headers'][_X_SIG].split('=', 1)

    if hash_algo not in hashlib.algorithms_guaranteed:
        raise KeyError(f'Hash algorithm "{hash_algo}" is not available')

    signature = hmac.new(_GITHUB_SECRET, event['body'].encode(), hash_algo)

    hexdigest = signature.hexdigest()

    if hexdigest != hash_value:
        raise KeyError(f'Incorrect GitHub Signature; given: {hash_value}; computed: {hexdigest}')

    # return event_name, deserialized_json
    # this won't work if the json keys are not allowed in namedtuple
    return (event['headers'][_X_EVENT], \
            json.loads(event['body'], \
                object_hook=lambda d: namedtuple('WebHook', \
                    [k+'_' for k in d.keys()]) (*d.values()) ))

def respond(err):
    return {
        'statusCode' : '400' if err else '200',
        'body' : str(err) if err else None,
        'headers' : { 'Content-Type': 'text/plain' }
    }

def lambda_handler(event, context):
    if _DEBUG: print('Received event: ' + json.dumps(event, indent=2))

    err = None

    try:
        parseGitHubWebHookEvent(event)
    except Exception as e:
        err = type(e).__name__ + ': ' + str(e)
        if _DEBUG:
            print(repr(traceback.format_exception( *(sys.exc_info()) )))

    return respond(err)

def parseGitHubWebHookEvent(event):
    (event_type, webhook) = getEventDetails(event)

    if _DEBUG:
        print(f'Event type = {event_type}')
    
    if event_type == 'issues':
        parseWebHookEventIssues(webhook)
    elif event_type == 'issue_comment':
        parseWebHookEventIssueComment(webhook)
    else:
        # should never come here
        pass

def parseWebHookEventIssues(webhook):
    if _DEBUG:
        print(f'Issues Action: {webhook.action_}')

    # new issue created
    if webhook.action_ == 'opened':
        subject = f'[{webhook.repository_.name_}] {webhook.issue_.title_}'
        text = f'{webhook.sender_.login_} created issue #{webhook.issue_.number_} in GitHub repo {webhook.repository_.full_name_}.\nURL: {webhook.issue_.html_url_}'

        tracker = Tracker()

        if _DEBUG:
            print(f'Creating ticket for {webhook.repository_.full_name_} / Issue id #{webhook.issue_.id_}.')

        ticket_id = tracker.createTicket(
                Requestor= _RT_REQUESTOR,
                Subject= subject,
                Text= text,
                files= [(f'issue_{webhook.issue_.id_}_comment_0.md', io.StringIO(webhook.issue_.body_), 'text/plain; charset=UTF-8')])

        if ticket_id == -1:
            raise RuntimeError('Ticket creation failed')

        if _DEBUG:
            print(f'Ticket id = {ticket_id}')
            print(f'Storing ticket RT#{ticket_id} as {webhook.repository_.full_name_} / Issue id #{webhook.issue_.id_}.')

        storeTicketNumber(webhook.repository_.full_name_, webhook.issue_.id_, ticket_id)
        if _DEBUG:
            print('Done.')
        return

    if webhook.action_ == 'closed':
        if _DEBUG:
            print(f'Retrieving Ticket number from {webhook.repository_.full_name_} / Issue id #{webhook.issue_.id_}.')

        ticket_id = getTicketNumber(webhook.repository_.full_name_, webhook.issue_.id_)   

        if _DEBUG:
            print(f'Resolving Ticket {ticket_id}.')

        Tracker().resolveTicket(ticket_id)
        if _DEBUG:
            print('Done.')
        return

    raise KeyError('Unimplemented issue action {webhook.action_}')

def parseWebHookEventIssueComment(webhook):
    if webhook.action_ not in ['created', 'edited', 'deleted']:
        raise KeyError('Unrecognised action {webhook.action_} in issue_comment')

    if _DEBUG:
        print(f'Issues Comments Action: {webhook.action_}')
        print(f'Retrieving Ticket number from {webhook.repository_.full_name_} / Issue id #{webhook.issue_.id_}.')

    ticket_id = getTicketNumber(webhook.repository_.full_name_, webhook.issue_.id_)   
    text = f'{webhook.sender_.login_} {webhook.action_} a comment in issue #{webhook.issue_.number_} in GitHub repo {webhook.repository_.full_name_}.\nURL: {webhook.comment_.html_url_}'

    if _DEBUG:
        print(f'Updating ticket, comment id #{webhook.comment_.id_}.')

    ret = Tracker().replyTicket(ticket_id, text= text, files=[ \
            (f'issue_{webhook.issue_.id_}_comment_{webhook.comment_.id_}.md', \
             io.StringIO(webhook.comment_.body_), \
             'text/plain; charset=UTF-8')])
    
    if ret == False:
        raise RuntimeError('Reply failed')

    if _DEBUG:
        print('Done.')
    return
