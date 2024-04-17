from django.db import models
import uuid

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.TextField(null=False)
    integrations = models.JSONField(null=False, default=dict)
