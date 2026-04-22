from flask import Flask, request, jsonify
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import uuid
import os
from datetime import datetime

app = Flask(__name__)

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
)
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'submissions'))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/submissions', methods=['POST'])
def create_submission():
    data = request.get_json()
    submission_id = str(uuid.uuid4())
    item = {
        'id': submission_id,
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'poster_filename': data.get('poster_filename', ''),
        'poster_s3_key': data.get('poster_s3_key', ''),
        'poster_content_type': data.get('poster_content_type', ''),
        'poster_size': data.get('poster_size', 0),
        'status': 'PENDING',
        'note': '',
        'created_at': datetime.utcnow().isoformat()
    }
    try:
        table.put_item(Item=item)
    except (BotoCoreError, ClientError) as exc:
        return jsonify({
            "error": "Failed to create submission",
            "detail": str(exc)
        }), 500
    return jsonify(item), 201

@app.route('/submissions/<submission_id>', methods=['GET'])
def get_submission(submission_id):
    try:
        response = table.get_item(Key={'id': submission_id})
    except (BotoCoreError, ClientError) as exc:
        return jsonify({
            "error": "Failed to get submission",
            "detail": str(exc)
        }), 500
    item = response.get('Item')
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item)

@app.route('/submissions/<submission_id>/file', methods=['PUT'])
def update_submission_file(submission_id):
    data = request.get_json() or {}
    try:
        table.update_item(
            Key={'id': submission_id},
            UpdateExpression=(
                'SET poster_filename = :f, poster_s3_key = :k, '
                'poster_content_type = :c, poster_size = :z'
            ),
            ExpressionAttributeValues={
                ':f': data.get('poster_filename', ''),
                ':k': data.get('poster_s3_key', ''),
                ':c': data.get('poster_content_type', ''),
                ':z': data.get('poster_size', 0)
            }
        )
    except (BotoCoreError, ClientError) as exc:
        return jsonify({
            "error": "Failed to update file metadata",
            "detail": str(exc)
        }), 500
    return jsonify({"message": "File metadata updated"})

@app.route('/submissions/<submission_id>', methods=['PUT'])
def update_submission(submission_id):
    data = request.get_json()
    try:
        table.update_item(
            Key={'id': submission_id},
            UpdateExpression='SET #s = :s, note = :n',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': data.get('status'),
                ':n': data.get('note', '')
            }
        )
    except (BotoCoreError, ClientError) as exc:
        return jsonify({
            "error": "Failed to update submission",
            "detail": str(exc)
        }), 500
    return jsonify({"message": "Updated"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
