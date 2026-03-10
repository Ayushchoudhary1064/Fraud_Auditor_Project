from django.db import models
from django.contrib.auth.models import AbstractUser

# Define the custom user model
class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.username

# Claim model
class Claim(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    claim_id = models.CharField(max_length=100, unique=True)
    patient_id = models.CharField(max_length=100)
    provider_id = models.CharField(max_length=100)
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # paid_amount is now entirely managed by the system (or left blank), not provided by user form
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    num_visits = models.IntegerField(null=True, blank=True)
    hospitalized = models.BooleanField(default=False)
    days_admitted = models.IntegerField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True) # Assuming this is claim-specific patient gender, not user gender
    procedure_code = models.CharField(max_length=100)
    diagnosis_code = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="Pending")
    notes = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Claim {self.claim_id} by {self.user.username}"