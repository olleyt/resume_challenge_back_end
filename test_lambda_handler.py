import unittest
import json
import boto3
import time
from aws_sso_lib import get_boto3_session
from moto import mock_dynamodb
from botocore.exceptions import ClientError

from update_visitor_counter_lambda import lambda_handler, get_item_attr, update_item

@mock_dynamodb
class TestLambdaFunction(unittest.TestCase):
    def setUp(self):
        # define these as environment variables:
        self.start_url  = 'https://d-9067a4ec77.awsapps.com/start'
        self.sso_region = 'us-east-1'
        self.account_id = '672961757886'
        self.role_name = 'PowerUserAccess'
        
        session = boto3.Session(profile_name='olley-sso-profile3')
        print('Created a session')
        print(session.client('sts').get_caller_identity())

        #sts = boto3.client('sts')
        #print(sts)
        #print(sts.get_caller_identity())
        
        #session = get_boto3_session(self.start_url, self.sso_region, self.account_id,
        #    self.role_name, *, self.sso_region, login=False, sso_cache=None, credential_cache=None)

        self.dynamodb = session.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'visitor_counter'
        self.partition_key = 'visitor_count'
        self.item_attribute = 'total_count'
        self.initial_value = 5
        
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': self.partition_key,
                 'KeyType': 'HASH'
                 }],
            AttributeDefinitions=[
                {'AttributeName': self.partition_key,
                 'AttributeType': 'S'
                 }],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )

        # Wait for the table to be created
        time.sleep(30)
        
        # Add initial value to the table
        self.table.put_item(
            Item={self.partition_key: self.item_attribute,
                  self.item_attribute: self.initial_value}
        )

        print('Successfully created a table and put item in it')
        
    def test_lambda_handler(self):
        event = {"table_name": "visitor_counter"}
        context = {}
        response = lambda_handler(event, context, self.dynamodb)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['count'], str(self.initial_value+1))
        
    #def test_get_item_attr(self):
    #    result = get_item_attr(self.table, self.partition_key, self.item_attribute)
    #    self.assertEqual(result, self.initial_value)
        
    #def test_update_item(self):
    #    new_value = 6
    #    status_code = update_item(self.table, self.partition_key, self.item_attribute, new_value)
    #    self.assertEqual(status_code, 200)
    #    self.assertEqual(get_item_attr(self.table, self.partition_key, self.item_attribute), new_value)

    #def test_get_item_attr_item_not_found(self):
    #    with self.assertRaises(KeyError):
    #        get_item_attr(self.table, 'not_found', 'not_found')
            
    #def test_update_item_provisioned_throughput_exceeded(self):
    #    with self.assertRaises(ClientError):
    #       update_item(self.table, self.partition_key, self.item_attribute, 6)
    

