import boto3
import json
import logging
import os
from botocore.exceptions import ClientError

# enable logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

#dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def get_item_attr(table_name, partition_key, item_attribute):
    """
        gets value of a specific attribute in a DynamoDB table by partition key
    """
    try:
        response = table_name.get_item(
            Key={ partition_key: item_attribute}
            )
    except ClientError as err:
        if err.response['Error']['Code'] == 'ValidationException':
            raise KeyError("Item not found")
        else:
            logger.error(
                "Couldn't get visitor counter from table %s. Here's why: %s: %s",
                table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
    else:        
        if 'Item' not in response:
            raise KeyError("Item not found")
        item = response['Item']
    
    return item[item_attribute]



def update_item (table_name, partition_key, item_attribute, new_value):
    """
    Updates item in DynamoDB table by partition key and attribute
    """
    status_code = 0
    
    try:
        update_response = table_name.update_item(
            Key={ partition_key: item_attribute},
            UpdateExpression='SET ' + item_attribute +' = :val1',
            ExpressionAttributeValues={':val1': new_value}
            )   
    except ClientError as err:
        # Check if the error is a provisioned throughput exceeded error
        if err.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
            raise
        else:
            logger.error(
                "Couldn't update visitor counter in the table %s. Here's why: %s: %s",
                table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
    else:       
        status_code = update_response['ResponseMetadata']['HTTPStatusCode']
    return status_code
        

def lambda_handler(event, context, session=None):
    if session is None:
        session = boto3.resource('dynamodb', region_name='us-east-1')

    table_name = os.environ.get('TABLE_NAME')
    table = session.Table(table_name)

    # get the total visitor count    
    total_visitor_count = get_item_attr(table, 'visitor_count', 'total_count')
    print(f'Total visitor count before update {total_visitor_count}')
    
    incremented_visitor_count = total_visitor_count + 1     
    status_code = update_item(table, 'visitor_count', 'total_count', incremented_visitor_count)
    
    updated_total_visitor_count = get_item_attr(table, 'visitor_count', 'total_count')
    message = { 'count': f'{updated_total_visitor_count}' }
        
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin" : "https://test.coolarchitect.link", # Required for CORS support to work 
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
            },
        'body': json.dumps(message)
    }