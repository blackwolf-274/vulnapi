from django.db import models
from django.contrib.auth.models import User

class ApiToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    action = models.CharField(max_length=100)
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)