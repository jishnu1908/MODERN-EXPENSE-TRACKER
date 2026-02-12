from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """Expense category model"""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='💰')
    color = models.CharField(max_length=7, default='#6366f1')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class Expense(models.Model):
    """Transaction model (Expense or Receivable)"""
    TRANSACTION_TYPE_CHOICES = [
        ('EXPENSE', 'Expense'),
        ('RECEIVABLE', 'Receivable'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('UPI', 'UPI'),
        ('CREDIT_CARD', 'Credit Card'),
        ('SLICE_BORROW', 'Slice Borrow'),
        ('CRED_CASH', 'Cred Cash'),
        ('EMI', 'EMI'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='expenses')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='EXPENSE')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ${self.amount}"
