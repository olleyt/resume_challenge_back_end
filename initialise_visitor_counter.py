import boto3
import json
import logging
import os
from botocore.exceptions import ClientError

# enable logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)


def init_counter(table_name, partition_key, item_attribute):
    """
        gets value of a counter attribute in the DynamoDB table by partition key
        if the item doesn't exist, it creates it with the counter attribute set to 0
    """
    try:
        response = table_name.get_item(
            Key={ partition_key: item_attribute}
            )
        item = response['Item'] 
        visit_count = item[item_attribute]   
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
            table_name.put_item(
                Item={
                    partition_key: item_attribute,
                    item_attribute: 0
                    })
        visit_count = 0
    
    return visit_count


if __name__ == '__main__':
    # initialise DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    # get the DynamoDB table
    table_name = os.environ.get('TABLE_NAME')
    table = dynamodb.Table(table_name)
    # initialise the counter
    init_counter(table, 'visitor_count', 'total_count')