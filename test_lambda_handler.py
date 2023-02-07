import unittest
import json
import boto3
import time
import logging
import os
from moto import mock_dynamodb
from botocore.exceptions import ClientError

#from update_visitor_counter_lambda import lambda_handler, get_item_attr, update_item
from lambda_function import lambda_handler, get_item_attr, update_item

# enable logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# initialise DynamoDB resource
@mock_dynamodb
class TestLambdaFunction(unittest.TestCase):
    def setUp(self):
        session = boto3.session.Session()
        print('Created a session')

        self.dynamodb = session.resource('dynamodb', region_name='us-east-1')
        self.table_name = os.environ.get('TABLE_NAME') 
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
        event = {"table_name": os.environ.get('TABLE_NAME')}
        context = {}
        table_name = os.environ.get('TABLE_NAME')
        initial_value = get_item_attr(self.dynamodb.Table(table_name), self.partition_key, self.item_attribute)
        self.assertEqual(initial_value, self.initial_value)
        
        response = lambda_handler(event, context, self.dynamodb)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['count'], str(initial_value+1))
        print('[OK] Successfully tested lambda_handler')
        
    def test_get_item_attr(self):
        result = get_item_attr(self.table, self.partition_key, self.item_attribute)
        self.assertEqual(result, self.initial_value)
        print('[OK] Successfully tested get_item_attr')
        
    def test_update_item(self):
        new_value = 6
        status_code = update_item(self.table, self.partition_key, self.item_attribute, new_value)
        self.assertEqual(status_code, 200)
        self.assertEqual(get_item_attr(self.table, self.partition_key, self.item_attribute), new_value)
        print('[OK] Successfully tested update_item')

    def test_get_item_attr_item_not_found(self):
        with self.assertRaises(KeyError):
            get_item_attr(self.table, 'not_found', 'not found')
        print('[OK] Successfully tested get_item_attr_item_not_found')    
            
    def test_update_item_provisioned_throughput_exceeded(self):
        # make multiple requests that exceed the table capacity
        for i in range(10):
            update_item(self.table, self.partition_key, self.item_attribute, i)
        print('[OK] Successfully tested update_item_provisioned_throughput_exceeded')    

    def tearDown(self):
        self.dynamodb.Table(self.table_name).delete()
        print('Successfully deleted the table')        
    
if __name__ == '__main__':
    unittest.main(failfast=True)
    print('Successfully tested all cases')
