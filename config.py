import boto3
import os
from base64 import b64decode
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

##config file containing credentials for rds mysql instance
rds_host  = os.environ['rds_host']
db_username = os.environ['db_username']
db_name = os.environ['db_name']

#Decrypt Secrets
ENCRYPTEDdb_password = os.environ['db_password']
db_password = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTEDdb_password))['Plaintext'].decode("utf-8") 

ENCRYPTEDslack_token = os.environ['slack_token']
slack_token = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTEDslack_token))['Plaintext'].decode("utf-8") 