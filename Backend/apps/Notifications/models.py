from django.db import models
from uuid import uuid4


# Create your models here.
class Notification(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
