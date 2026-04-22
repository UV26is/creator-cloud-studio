import json
import urllib.request
import boto3
import os

def get_ec2_public_ip(region='us-east-1'):
    """通过 EC2 tag（Project=creator-cloud-studio）动态查询 Public IP"""
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Project', 'Values': ['creator-cloud-studio']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            public_ip = instance.get('PublicIpAddress')
            if public_ip:
                print(f"Found EC2 instance with Public IP: {public_ip}")
                return public_ip
    raise Exception("No running EC2 instance found with tag Project=creator-cloud-studio")

def lambda_handler(event, context):
    """
    接收 Processing Function 算出的结果，
    动态查询 EC2 Public IP（通过 tag），
    用 HTTP PUT 请求更新 Data Service 里的记录。
    """

    print(f"Received result: {json.dumps(event)}")

    submission_id = event.get('submission_id')
    status = event.get('status')
    note = event.get('note')

    # 动态查询 EC2 Public IP
    region = os.environ.get('AWS_REGION', 'us-east-1')
    ec2_ip = get_ec2_public_ip(region=region)
    data_service_url = f"http://{ec2_ip}:5001"
    print(f"Data Service URL (from EC2 tag): {data_service_url}")

    update_data = json.dumps({
        'status': status,
        'note': note
    }).encode('utf-8')

    url = f"{data_service_url}/submissions/{submission_id}"
    req = urllib.request.Request(
        url,
        data=update_data,
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"Data Service updated: {result}")
    except Exception as e:
        print(f"Error updating Data Service: {str(e)}")
        raise e

    print(f"Successfully updated submission {submission_id} to {status}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'submission_id': submission_id,
            'status': status,
            'updated': True
        })
    }
