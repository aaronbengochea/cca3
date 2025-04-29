import json
import requests
from requests_aws4auth import AWS4Auth
import boto3
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Set up your AWS Elasticsearch (OpenSearch) domain endpoint and region
ES_ENDPOINT = os.getenv("ES_ENDPOINT")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASS")

INDEX = "photos"  
region = 'us-east-1'
service = 'es'

# Get AWS credentials using boto3
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key,
                   credentials.secret_key,
                   region,
                   service,
                   session_token=credentials.token)


def create_index():
    """
    Creates an Elasticsearch index called "restaurants" with the mapping for RestaurantID and Cuisine.
    Note: We remove the custom type name and define properties directly.
    """
    print(ES_ENDPOINT)

    url = f"{ES_ENDPOINT}/{INDEX}"
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
        },
        "mappings": {
            "properties": {
                "objectKey": {"type": "keyword"},
                "bucket": {"type": "keyword"},
                "createdTimestamp": {"type": "date"},
                "labels": {"type": "keyword"},
            }
        }
    }
    response = requests.put(url, auth=(ES_USER, ES_PASS), json=index_settings)
    if response.status_code in (200, 201):
        print("Index created successfully.")
    else:
        print(f"Error creating index: {response.status_code} {response.text}")


if __name__ == "__main__":
    create_index()



