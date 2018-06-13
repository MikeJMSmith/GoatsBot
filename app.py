import sys
import logging
import config
import pymysql
from slackclient import SlackClient
import boto3


import json
import dateutil.parser
import datetime
import time
import os
import math
import random


#rds settings
rds_host  = config.rds_host
name = config.db_username
password = config.db_password
db_name = config.db_name


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def openConnection():
    """ 
    Opens the connection to RDS 
    """
    try:
        logger.info(">>> Connecting to RDS")
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=3)
        return conn
        logger.info(">>> SUCCESS: Connection to RDS mysql instance succeeded")
    except:
        logger.error(">>> ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()    

def createSlackConnection():
    """ 
    creates the SlackAPI object 
    """
    sc = SlackClient(config.slack_token)
    return sc

def countFineTotal():
    conn = openConnection()
    sc = createSlackConnection()
    userFines = {}
    
    with conn.cursor() as cur:
        cur.execute("select userid, count(*) as Fines from tblFines group by userid")
    for row in cur:
        result = sc.api_call("users.info",user=row[0])
        username = result["user"]["profile"]["first_name"]
        lastName = result["user"]["profile"]["last_name"]
        userFines[username + " " + lastName] = row[1]
    logger.info(">>> " + str(userFines))
    return userFines
    
""" --- Responses --- """

def respondQuote(intent_request):
    Quote = ""

    randomQuoteID = random.randrange(1, 8)
    conn = openConnection()
    with conn.cursor() as cur:
        cur.execute("select Quote from tblQuotes where id=" + str(randomQuoteID))
        for row in cur:
            quote = row[0]
            #logger.info(row)
    return {"sessionAttributes":{
    
    },
  "dialogAction": {
    "type": "Close",
    "fulfillmentState": "Fulfilled",
    "message": {
      "contentType": "PlainText",
      "content": "'" + quote + "'"
        }
    }
}
    
def respondFinesTotal(intent_request):
    """ 
    Captures fine total for current user
    """
    #sc = createSlackConnection()
    
    #userid = intent_request['userId'].split(":")[2]
    fineCount = countFineTotal()
    message = ""
    
    for key in fineCount:
        message = message + " " + str(key) + " has " + str(fineCount[key]) + " dollars in fines. " + "\n"
        #"{}: {}".format(key, transaction[key])
        logger.info(">>> " + str(key))
        logger.info(">>> " + str(fineCount[key]))
        
    
    return {"sessionAttributes":{
    
    },
  "dialogAction": {
    "type": "Close",
    "fulfillmentState": "Fulfilled",
    "message": {
      "contentType": "PlainText",
      "content": "The following people have fines: \n" + message
        }
    }
}
    
def respondregisterFine(intent_request):
    """ 
    Functions that control the bot's behavior 
    """
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('tblFines')
    
    
    sc = createSlackConnection()
    
    userid = intent_request['userId'].split(":")[2]
    
    result = sc.api_call("users.info",user=userid)
    username = result["user"]["profile"]["first_name"]
    
    conn = openConnection()
    with conn.cursor() as cur:
        cur.execute('insert into tblFines (userid, fineamount) values("'+userid+'", 1.00)')
        conn.commit()
    
    table.put_item(
    Item={
        'epochTime': int(time.time()),
        'UserID': userid,
        'fineAmount': 1,
        'userName': username
        }
    )
    
    #fineCount = countFineTotal(intent_request, userid)
    
    return {"sessionAttributes":{
    
    },
  "dialogAction": {
    "type": "Close",
    "fulfillmentState": "Fulfilled",
    "message": {
      "contentType": "PlainText",
      "content": "Hello, " + username + ". You have been fined!" 
        }
    }
}

""" --- Intents --- """

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    
    logger.info('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'Fines':
        return respondregisterFine(intent_request)
    elif intent_name == 'getCurrentFines':
        return respondFinesTotal(intent_request)
    elif intent_name == 'getQuote':
        return respondQuote(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')
    

""" --- Main handler --- """

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)