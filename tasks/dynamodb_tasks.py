import uuid
import boto3
from django.conf import settings
from datetime import datetime, timezone

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=settings.AWS_REGION
)

task_table = dynamodb.Table(settings.DDB_TASK_TABLE)


# Create a new task
def create_task(data):
    task_id = str(uuid.uuid4())

    # Convert datetime to string (ISO format)
    due_date = data["due_date"].isoformat()

    item = {
        "task_id": task_id,
        "title": data["title"],
        "description": data["description"],
        "assigned_to": data["assigned_to"],
        "created_by": data["created_by"],
        "status": "PENDING",
        "due_date": due_date,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    task_table.put_item(Item=item)
    return task_id

# Get ALL tasks
def get_all_tasks():
    response = task_table.scan()
    return response.get("Items", [])


# Get task by ID
def get_task(task_id):
    response = task_table.get_item(Key={"task_id": task_id})
    return response.get("Item")


# Update task
def update_task(task_id, data):

    # Convert datetime to ISO string
    due_date = data["due_date"].isoformat()

    task_table.update_item(
        Key={"task_id": task_id},
        UpdateExpression="""
            SET title=:t,
                description=:d,
                assigned_to=:a,
                status=:s,
                due_date=:due,
                updated_at=:u
        """,
        ExpressionAttributeValues={
            ":t": data["title"],
            ":d": data["description"],
            ":a": data["assigned_to"],
            ":s": data["status"],
            ":due": due_date,
            ":u": datetime.utcnow().isoformat(),
        }
    )


# Delete task
def delete_task(task_id):
    task_table.delete_item(Key={"task_id": task_id})
