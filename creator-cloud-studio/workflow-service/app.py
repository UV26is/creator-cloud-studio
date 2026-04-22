from flask import Flask, request, jsonify
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import requests
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

s3 = boto3.client('s3', region_name='us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET', 'creato-rcloud-22207672')

# EC2 上所有服务共用同一台主机，通过环境变量传入 Public IP
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://localhost:5001')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/submit', methods=['POST'])
def submit():
    is_multipart = request.content_type and request.content_type.startswith('multipart/form-data')
    data = request.form if is_multipart else (request.get_json() or {})
    title = data.get('title', '')
    description = data.get('description', '')
    poster_file = request.files.get('poster_file') if is_multipart else None
    poster_filename = secure_filename(poster_file.filename) if poster_file and poster_file.filename else data.get('poster_filename', '')
    poster_content_type = poster_file.mimetype if poster_file else ''
    poster_size = 0

    print(f"Data Service URL: {DATA_SERVICE_URL}")

    response = requests.post(
        f'{DATA_SERVICE_URL}/submissions',
        json={
            'title': title,
            'description': description,
            'poster_filename': poster_filename
        }
    )
    if not response.ok:
        return jsonify({
            "error": "Data service failed to create submission",
            "detail": response.text
        }), response.status_code
    submission = response.json()
    submission_id = submission['id']

    poster_s3_key = ''
    if poster_file and poster_filename:
        poster_s3_key = f'posters/{submission_id}/{poster_filename}'
        poster_file.stream.seek(0, os.SEEK_END)
        poster_size = poster_file.stream.tell()
        poster_file.stream.seek(0)
        try:
            s3.upload_fileobj(
                poster_file.stream,
                S3_BUCKET,
                poster_s3_key,
                ExtraArgs={
                    'ContentType': poster_content_type or 'application/octet-stream'
                }
            )
        except (BotoCoreError, ClientError) as exc:
            return jsonify({
                "error": "Failed to upload poster file",
                "detail": str(exc)
            }), 500

    s3_key = f'submissions/{submission_id}.json'
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps({
                'submission_id': submission_id,
                'title': title,
                'description': description,
                'poster_filename': poster_filename,
                'poster_s3_key': poster_s3_key,
                'poster_content_type': poster_content_type,
                'poster_size': poster_size
            }),
            ContentType='application/json'
        )
    except (BotoCoreError, ClientError) as exc:
        return jsonify({
            "error": "Failed to create submission event",
            "detail": str(exc)
        }), 500

    if poster_s3_key:
        file_response = requests.put(
            f'{DATA_SERVICE_URL}/submissions/{submission_id}/file',
            json={
                'poster_filename': poster_filename,
                'poster_s3_key': poster_s3_key,
                'poster_content_type': poster_content_type,
                'poster_size': poster_size
            }
        )
        if not file_response.ok:
            return jsonify({
                "error": "Data service failed to update file metadata",
                "detail": file_response.text
            }), file_response.status_code

    return jsonify({
        "submission_id": submission_id,
        "message": "Submission received, processing started"
    }), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
