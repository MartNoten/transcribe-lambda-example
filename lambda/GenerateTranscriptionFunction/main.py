import json
import urllib.parse
import boto3
import time
import requests
import os

TRANSCRIPT_BUCKET = os.environ['TRANSCRIPT_BUCKET']

def handler(event, context):
    print("Started Lambda function")

    ## Reading the invocation file and starting the Amazon Transcribe job
    bucket, key = get_bucket_key(event)
    result_s3_location = start_transcript_job(bucket, key)
    print(f"Going to download result from {result_s3_location}")

    ## Read the Transcribe results and store it locally
    local_json_file_location = download_file(result_s3_location)
    print(f"We stored the result locally under {local_json_file_location}")

    ## Get the transcript from the Transcribe result
    transcript = read_transcript_from_job_result(local_json_file_location)
    print(f'Got transcript: {transcript}')
    
    ## Upload the transcript in a new S3 bucket
    uploaded = store_transcript_in_s3(local_json_file_location, transcript)
    if uploaded:
        print("Succesfully uploaded to S3")
    else:
        print('We did not upload the transcript to the destination bucket')

    print('Finished Lambda function')


def get_bucket_key(event):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    return bucket, key


def download_file(url):
    try:
        file_name = "/tmp/" + url.split("/")[-1].split("?")[0]
        r = requests.get(url, allow_redirects=True)
        open(file_name, 'wb').write(r.content)
        return file_name
    except Exception as e:
        print(e)
        print(f'Could not download file from {url}')
        raise e

def store_transcript_in_s3(file_name, transcript):
    txt_file_name = file_name.split(".")[0]+".txt"
    print(f"Going to store transcript under {txt_file_name}")
    with open(txt_file_name, 'w') as f:
        f.write(transcript)


    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(txt_file_name, TRANSCRIPT_BUCKET, txt_file_name.split("/")[2])
    except ClientError as e:
        logging.error(e)
        return False
    return True
    

def read_transcript_from_job_result(file_location):
    f = open(file_location)
    data = json.load(f)
    print(data)
    f.close()
    return data['results']['transcripts'][0]['transcript']

def start_transcript_job(bucket, key):
    transcribe = boto3.client('transcribe')
    job_name = f"{bucket}-{key}"
    job_uri = f"s3://{bucket}/{key}"
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='mp3',
        LanguageCode='en-US'
    )

    while True:
        status = transcribe.get_transcription_job(
            TranscriptionJobName=job_name)
        print(status)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            print('Finished!')
            return status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        else:
            print("Not ready yet...")
            time.sleep(5)
