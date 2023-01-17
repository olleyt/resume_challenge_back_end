import unittest
import json
import boto3
import time
import logging
from aws_sso_lib import get_boto3_session
from moto import mock_dynamodb
from botocore.exceptions import ClientError

from update_visitor_counter_lambda import lambda_handler, get_item_attr, update_item

# enable logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

@mock_dynamodb
class TestLambdaFunction(unittest.TestCase):
    def setUp(self):
        
        session = boto3.Session(profile_name='olley-sso-profile3')
        print('Created a session')
        # print(session.client('sts').get_caller_identity())

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
        
    def test_get_item_attr(self):
        result = get_item_attr(self.table, self.partition_key, self.item_attribute)
        self.assertEqual(result, self.initial_value)
        
    def test_update_item(self):
        new_value = 6
        status_code = update_item(self.table, self.partition_key, self.item_attribute, new_value)
        self.assertEqual(status_code, 200)
        self.assertEqual(get_item_attr(self.table, self.partition_key, self.item_attribute), new_value)

    def test_get_item_attr_item_not_found(self):
        with self.assertRaises(KeyError):
            get_item_attr(self.table, 'not_found', 'not found')
            
    def test_update_item_provisioned_throughput_exceeded(self):
        # make multiple requests that exceed the table capacity
        for i in range(10):
            update_item(self.table, self.partition_key, self.item_attribute, i)

    def tearDown(self):
        self.dynamodb.Table(self.table_name).delete()        
    

