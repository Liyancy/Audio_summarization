# lambda_function.py
import json
import os
import time
import boto3
import requests
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Extract bucket name and object key from the event
    try:
        record = event['Records'][0]['s3']
        bucket_name = record['bucket']['name']
        object_key = record['object']['key']
    except (KeyError, IndexError) as e:
        return {"statusCode": 400, "body": f"Malformed event data: {str(e)}"}

    # Initialize S3 client
    s3 = boto3.client('s3')

    # Download transcription file content
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        transcription_text = response['Body'].read().decode('utf-8')
    except ClientError as e:
        return {"statusCode": 500, "body": f"Failed to download S3 object: {str(e)}"}

    # Prepare RunPod request
    runpod_api_key = os.environ.get("RUNPOD_API_KEY")
    endpoint_url = os.environ.get("RUNPOD_ENDPOINT_URL")  # Provided at deployment

    headers = {
        "Authorization": f"Bearer {runpod_api_key}",
        "Content-Type": "application/json"
    }

    run_payload = {
        "input": {
            "prompt": f"Summarize the following text in approximately 4000 words:\n{transcription_text}",
            "max_tokens": 16000  # Adjust based on model capability
        }
    }

    try:
        run_response = requests.post(f"{endpoint_url}/run", headers=headers, json=run_payload)
        run_response.raise_for_status()
        run_id = run_response.json().get("id")
    except requests.RequestException as e:
        return {"statusCode": 500, "body": f"RunPod run request failed: {str(e)}"}

    # Poll /status endpoint for result
    max_wait_time = 600  # seconds
    poll_interval = 10
    elapsed = 0
    summary = None

    while elapsed < max_wait_time:
        try:
            status_response = requests.get(f"{endpoint_url}/status/{run_id}", headers=headers)
            status_response.raise_for_status()
            result = status_response.json()
            if result.get("status") == "COMPLETED":
                summary = result.get("output")
                break
            elif result.get("status") == "FAILED":
                return {"statusCode": 500, "body": "RunPod job failed."}
        except requests.RequestException as e:
            return {"statusCode": 500, "body": f"Polling failed: {str(e)}"}

        time.sleep(poll_interval)
        elapsed += poll_interval

    if summary is None:
        return {"statusCode": 504, "body": "RunPod summarization job timed out."}

    # Save the summary back to a designated S3 location
    output_bucket = os.environ.get("OUTPUT_BUCKET_NAME", bucket_name)
    output_key = f"summaries/{os.path.basename(object_key).replace('.txt', '_summary.txt')}"

    try:
        s3.put_object(Bucket=output_bucket, Key=output_key, Body=summary.encode('utf-8'))
    except ClientError as e:
        return {"statusCode": 500, "body": f"Failed to upload summary to S3: {str(e)}"}

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Summarization completed and uploaded successfully.",
            "summary_s3_key": output_key
        })
    }



