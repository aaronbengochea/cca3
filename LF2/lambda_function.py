import os
import json
import uuid
import boto3
import requests

# Initialize AWS clients and configuration
lex_client = boto3.client('lexv2-runtime')

ES_ENDPOINT = os.environ['ES_ENDPOINT']    
ES_USER     = os.environ['ES_USER']        
ES_PASS     = os.environ['ES_PASS']       
ES_HEADERS  = {"Content-Type": "application/json"}

LEX_BOT_ID       = os.environ['LEX_BOT_ID']
LEX_BOT_ALIAS_ID = os.environ['LEX_BOT_ALIAS_ID']
LEX_LOCALE_ID    = os.environ['LEX_LOCALE_ID']


def lambda_handler(event, context):
    # 1) Extract query parameter from API Gateway
    params = event.get('queryStringParameters') or {}
    query = params.get('q', '').strip()
    if not query:
        return {'statusCode': 200, 'body': json.dumps({'results': []})}

    # 2) Send text to Lex to extract keywords
    session_id = str(uuid.uuid4())
    try:
        lex_resp = lex_client.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId=LEX_LOCALE_ID,
            sessionId=session_id,
            text=query
        )
    except Exception as e:
        print(f"Lex error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'code': 500, 'message': 'Failed to process query'})}

    # 3) Extract multi-value slot 'Label'
    slots      = lex_resp.get('sessionState', {}).get('intent', {}).get('slots', {})
    label_slot = slots.get('Label', {})
    values     = label_slot.get('values', []) or []
    keywords   = [v.get('value', {}).get('interpretedValue', '').lower() for v in values]

    if not keywords:
        return {'statusCode': 200, 'body': json.dumps({'results': []})}

    # 4) Query OpenSearch for matching labels
    es_url = f"https://{ES_ENDPOINT}/photos/_search"
    es_query = {
        'query': {
            'terms': {
                'labels': keywords
            }
        }
    }
    try:
        es_resp = requests.get(es_url, auth=(ES_USER, ES_PASS), headers=ES_HEADERS, json=es_query)
        es_resp.raise_for_status()
        hits = es_resp.json().get('hits', {}).get('hits', [])
    except Exception as e:
        print(f"OpenSearch error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'code': 500, 'message': 'Search failed'})}

    # 5) Build response array of Photo objects
    results = []
    for hit in hits:
        src    = hit.get('_source', {})
        bucket = src.get('bucket')
        key    = src.get('objectKey')
        url    = f"https://{bucket}.s3.amazonaws.com/{key}"
        labels = src.get('labels', [])
        results.append({'url': url, 'labels': labels})

    # 6) Return as per API spec
    return {
        'statusCode': 200,
        'body': json.dumps({'results': results})
    }