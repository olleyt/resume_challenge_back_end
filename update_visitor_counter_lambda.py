import boto3
import json

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    table = dynamodb.Table('visitor_counter')

    # only for 1st time
    #response = table.put_item(
    #    Item={
    #        'visitor_count': 0
    #    }
    #)
    
    # get the total visitor count
    try:
        response = table.get_item(
            Key={ 'visitor_count': 'total_count'}
            )
    except ClientError as err:
            logger.error(
                "Couldn't get visitor counter from table %s. Here's why: %s: %s",
                self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
    else:        
        item = response['Item']
    
    total_visitor_count = item['total_count']
    print(f'Total visitor count before update {total_visitor_count}')
    
    incremented_visitor_count = total_visitor_count + 1
    
    table.update_item(
    Key={'visitor_count': 'total_count'},
    UpdateExpression='SET total_count = :val1',
    ExpressionAttributeValues={
        ':val1': incremented_visitor_count
        }
    )
    
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    #print(f'Status code: {status_code}')
    
    print(f'Total visitor count after update {incremented_visitor_count}')
    
    message = {
        'message': 'Execution started successfully!'
        }
        
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(message)
    }