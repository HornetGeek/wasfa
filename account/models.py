from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
# Create your models here.
# Create your views here.
from django.contrib.auth.models import User

class CustomUserManager(BaseUserManager):
    """

    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        print(self.model)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save()
        print("userrrr")
        print(user)
        print(user.password)
        return user
    

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
    

class CustomUsers(AbstractBaseUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('pharmacy', 'Pharmacy'),
    )

    username = None
    created_at = models.DateTimeField("Created at", auto_now=True)
    email = models.EmailField('email address', unique=True)
    fullName = models.CharField(max_length=255, default='')
    civil_number = models.CharField(max_length=255, default='')
    Practice_License_Number = models.CharField(max_length=255, default='')
    fcm_token = models.CharField(max_length=255, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='doctor')
    blocked = models.BooleanField(default=False) 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    

class Patient(models.Model):
    doctorId = models.ForeignKey(CustomUsers, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='')
    idNumber = models.CharField(max_length=255, default='')
    phone_number = models.CharField(max_length=255, default='')


class Prescription(models.Model):
    TYPE_CHOICES = [
        ('internal', 'باطنه'),
        ('surgery', 'جراحة'),
        ('pediatric', 'أطفال'),
        # Add more types as needed
    ]
    doctorId = models.ForeignKey(CustomUsers, on_delete=models.CASCADE)
    patientId = models.ForeignKey(Patient, on_delete=models.CASCADE)
    created_at = models.DateTimeField("Created at", auto_now=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='internal')

class Drug(models.Model):
    prescriptionId = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='')