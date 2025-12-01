from django.db import models
from django.contrib.auth.models import User

# This model adds a role to each user
class EmployeeProfile(models.Model):

    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("EMPLOYEE", "Employee"),
    ]

    # Connect to Django's User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Assign a role
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="EMPLOYEE"
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"
