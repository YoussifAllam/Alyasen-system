from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone


class UserTypeChoice(models.TextChoices):
    ADMIN = "Admin"
    Accountant = "Accountant"


class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    email_verified = models.BooleanField(default=True)
    otp = models.IntegerField(default=0)
    otp_created_at = models.DateTimeField(auto_now_add=True)
    created_Date = models.DateField(default=timezone.now)
    last_login = models.DateTimeField(auto_now_add=True)
    is_approvid = models.BooleanField(default=False)
    user_type = models.CharField(
        max_length=20, choices=UserTypeChoice.choices, default=UserTypeChoice.Accountant
    )
    password = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    reset_password_token = models.CharField(max_length=50, default="", blank=True)
    reset_password_expire = models.DateTimeField(null=True, blank=True)
