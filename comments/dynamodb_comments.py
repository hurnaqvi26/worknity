import uuid
import boto3
from django.conf import settings
from datetime import datetime

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=settings.AWS_REGION
)

comment_table = dynamodb.Table(settings.DDB_COMMENT_TABLE)


# Add a new comment
def create_comment(task_id, username, content):
    comment_id = str(uuid.uuid4())

    item = {
        "comment_id": comment_id,
        "task_id": task_id,
        "username": username,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
    }

    comment_table.put_item(Item=item)
    return comment_id


# Get comments for one task
def get_comments_for_task(task_id):
    response = comment_table.scan(
        FilterExpression="task_id = :t",
        ExpressionAttributeValues={":t": task_id}
    )
    return response.get("Items", [])
