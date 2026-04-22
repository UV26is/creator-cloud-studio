import json
import boto3
import urllib.parse
import os

# 用来呼叫其他 Lambda 函数
lambda_client = boto3.client(
    'lambda',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# S3 客户端，用来读取上传的文件内容
s3_client = boto3.client(
    's3',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# Processing Function 的名称（从环境变量读取）
PROCESSING_FUNCTION = os.environ.get(
    'PROCESSING_FUNCTION_NAME',
    'processing-function'
)

def lambda_handler(event, context):
    """
    这个函数被 S3 触发。
    S3 上传了一个 JSON 文件后，会把事件资讯传进来。
    我们的工作是：
    1. 从 S3 读取那个 JSON 文件的内容
    2. 转发给 Processing Function 处理
    """

    # 从 S3 事件里拿到 bucket 名称和文件路径
    # 这个格式跟 Lab 3 里学的一模一样！
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        record['s3']['object']['key'],
        encoding='utf-8'
    )

    print(f"Triggered by S3 upload: bucket={bucket}, key={key}")

    if not key.startswith('submissions/') or not key.endswith('.json'):
        print(f"Ignoring non-submission metadata object: {key}")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored non-submission object'})
        }

    # 从 S3 读取文件内容
    s3_response = s3_client.get_object(Bucket=bucket, Key=key)
    submission_data = json.loads(
        s3_response['Body'].read().decode('utf-8')
    )

    print(f"Submission data: {json.dumps(submission_data)}")

    # 把 submission 资料转发给 Processing Function
    # 这里用 Lambda invoke 直接呼叫另一个 Lambda
    lambda_client.invoke(
        FunctionName=PROCESSING_FUNCTION,
        InvocationType='Event',  # 非同步呼叫，不等结果
        Payload=json.dumps(submission_data)
    )

    print(f"Forwarded to Processing Function: {PROCESSING_FUNCTION}")

    return {
        'statusCode': 200,
        'body': json.dumps('Submission event processed')
    }
