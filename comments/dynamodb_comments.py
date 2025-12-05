import uuid
import boto3
from django.conf import settings
from datetime import datetime, timezone
import os

# Connect to DynamoDB

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

comment_table = dynamodb.Table(settings.DDB_COMMENT_TABLE)


# Add a new comment
def create_comment(task_id, username, content):
    comment_id = str(uuid.uuid4())

    item = {
        "comment_id": comment_id,
        "task_id": task_id,
        "username": username,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
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

def add_comment(task_id, author, text):
    """
    Cloud mode: Save a comment for a task in DynamoDB.
    """
    table = dynamodb.Table("comments")

    item = {
        "comment_id": str(uuid.uuid4()),
        "task_id": task_id,
        "author": author,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=item)
    return item
