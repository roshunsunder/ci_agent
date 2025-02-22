from dotenv import load_dotenv
import os
import boto3
# Create a DynamoDB client
load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('REGION_NAME')
)

public_companies_table = dynamodb.Table('public_companies')
users_table = dynamodb.Table('users')
agents_table = dynamodb.Table('agents')