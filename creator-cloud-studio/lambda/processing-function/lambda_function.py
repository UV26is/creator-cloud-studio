import json
import boto3
import os

lambda_client = boto3.client(
    'lambda',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# Result Update Function 的名称
RESULT_UPDATE_FUNCTION = os.environ.get(
    'RESULT_UPDATE_FUNCTION_NAME',
    'result-update-function'
)

def check_submission(title, description, poster_filename):
    """
    核心审核逻辑，完全按照老师的规则：

    规则一（最优先）：有任何必填栏位是空的 → INCOMPLETE
    规则二：全部有填，但 description 少于 30 字，
            或 filename 不是 .jpg/.jpeg/.png → NEEDS REVISION
    规则三：全部合格 → READY
    """

    # 规则一：检查必填栏位
    # 只要有任何一个是空的，直接返回 INCOMPLETE
    # 不再检查其他规则
    if not title or not description or not poster_filename:
        missing = []
        if not title:
            missing.append('title')
        if not description:
            missing.append('description')
        if not poster_filename:
            missing.append('poster filename')
        return (
            'INCOMPLETE',
            f"Missing required fields: {', '.join(missing)}. "
            f"Please fill in all fields."
        )

    # 到这里代表所有栏位都有填
    # 规则二：检查 description 长度和 filename 格式
    issues = []

    # 检查 description 是否至少 30 个字元
    if len(description) < 30:
        issues.append(
            f"description too short ({len(description)} chars, need 30)"
        )

    # 检查 poster filename 是否以 .jpg/.jpeg/.png 结尾
    valid_extensions = ('.jpg', '.jpeg', '.png')
    if not poster_filename.lower().endswith(valid_extensions):
        issues.append(
            f"poster filename must end with .jpg, .jpeg, or .png"
        )

    # 如果有任何问题，返回 NEEDS REVISION
    if issues:
        return (
            'NEEDS REVISION',
            f"Please fix the following: {'; '.join(issues)}."
        )

    # 规则三：全部合格
    return (
        'READY',
        "Your poster submission looks great! "
        "It is ready to be published."
    )

def lambda_handler(event, context):
    """
    接收 Submission Event Function 转发来的资料，
    执行审核规则，把结果传给 Result Update Function。
    """

    print(f"Received submission: {json.dumps(event)}")

    # 拿出提交的资料
    submission_id = event.get('submission_id', '')
    title = event.get('title', '')
    description = event.get('description', '')
    poster_filename = event.get('poster_filename', '')

    # 执行审核规则
    status, note = check_submission(title, description, poster_filename)

    print(f"Result: status={status}, note={note}")

    # 把结果传给 Result Update Function
    result_data = {
        'submission_id': submission_id,
        'status': status,
        'note': note
    }

    lambda_client.invoke(
        FunctionName=RESULT_UPDATE_FUNCTION,
        InvocationType='Event',  # 非同步呼叫
        Payload=json.dumps(result_data)
    )

    print(f"Forwarded result to Result Update Function")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'submission_id': submission_id,
            'status': status,
            'note': note
        })
    }