import os
import json
import boto3
import requests
from datetime import datetime

# ─── Clients ─────────────────────────────────────────────────────────────────────
region = os.environ.get("AWS_REGION", "us-east-1")

s3      = boto3.client("s3")
rekog   = boto3.client("rekognition")

# ─── ES HTTP AUTH SETUP ──────────────────────────────────────────────────────────
ES_ENDPOINT = os.environ["ES_ENDPOINT"]     # e.g. "search-photos-abc123.us-east-1.es.amazonaws.com"
ES_USER     = os.environ["ES_USER"]         # HTTP auth username
ES_PASS     = os.environ["ES_PASS"]         # HTTP auth password

def lambda_handler(event, context):
    for record in event.get("Records", []):
        if not record.get("eventName", "").startswith("ObjectCreated:Put"):
            continue

        bucket = record["s3"]["bucket"]["name"]
        key    = record["s3"]["object"]["key"]

        # 1) Rekognition: detect labels
        rk = rekog.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=20,
            MinConfidence=75,
        )
        auto_labels = [lbl["Name"] for lbl in rk.get("Labels", [])]

        # 2) HeadObject: pull any x-amz-meta-customlabels
        hdr = s3.head_object(Bucket=bucket, Key=key)
        raw  = hdr.get("Metadata", {}).get("customlabels", "")
        custom_labels = [c.strip() for c in raw.split(",") if c.strip()]

        # 3) Merge, lowercase & dedupe
        labels = list({lbl.lower() for lbl in (*auto_labels, *custom_labels)})

        # 4) Build the document
        doc = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimestamp": datetime.utcnow().isoformat(),
            "labels": labels,
        }

        # 5) Index via HTTP PUT
        #    URL-encode key if necessary; here we just interpolate 
        url = f"https://{ES_ENDPOINT}/photos/_doc/{bucket}/{key}"
        headers = {"Content-Type": "application/json"}

        resp = requests.put(
            url,
            auth=(ES_USER, ES_PASS),
            headers=headers,
            json=doc
        )

        if resp.ok:
            print(f"Indexed {bucket}/{key} →", resp.json())
        else:
            print(f"Failed to index {bucket}/{key}:",
                  resp.status_code, resp.text)
            resp.raise_for_status()

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Processing complete"})
    }
