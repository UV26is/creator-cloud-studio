from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# EC2 上所有服务共用同一台主机，通过环境变量传入 Public IP
WORKFLOW_SERVICE_URL = os.environ.get('WORKFLOW_SERVICE_URL', 'http://localhost:5002')
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://localhost:5001')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        poster_file = request.files.get('poster_file')
        files = None
        if poster_file and poster_file.filename:
            files = {
                'poster_file': (
                    poster_file.filename,
                    poster_file.stream,
                    poster_file.mimetype or 'application/octet-stream'
                )
            }
        response = requests.post(
            f'{WORKFLOW_SERVICE_URL}/submit',
            data={
                'title': request.form.get('title', ''),
                'description': request.form.get('description', '')
            },
            files=files
        )
    else:
        data = request.get_json()
        response = requests.post(f'{WORKFLOW_SERVICE_URL}/submit', json=data)
    try:
        payload = response.json()
    except ValueError:
        payload = {
            "error": "Workflow service returned a non-JSON response",
            "detail": response.text
        }
    return jsonify(payload), response.status_code

@app.route('/result/<submission_id>', methods=['GET'])
def get_result(submission_id):
    response = requests.get(f'{DATA_SERVICE_URL}/submissions/{submission_id}')
    try:
        payload = response.json()
    except ValueError:
        payload = {
            "error": "Data service returned a non-JSON response",
            "detail": response.text
        }
    return jsonify(payload), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
