from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer
from .models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUsers  # Use CustomUsers directly
        fields = ('id', 'email', 'fullName','password', 'created_at', 'fcm_token', "civil_number","Practice_License_Number","role" )    



class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUsers  # Use CustomUsers directly
        fields = ('id', 'email', 'fullName', 'created_at', 'fcm_token', "civil_number","Practice_License_Number","role" )    



class CustomTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        print(email)
        if not email or not password:
            raise serializers.ValidationError('Both email and password are required')
        
        user = CustomUsers.objects.filter(email=email).first()
        print(user)
        if not user:
            raise serializers.ValidationError('No active account found with the given credentials')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials')

        # Return user object in validated data for token creation
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'email': user.email,
        }
    

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('id', 'doctorId', 'name', 'idNumber', 'phone_number')


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'doctorId', 'patientId', 'type', 'created_at']


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = ['id', 'prescriptionId', 'name']
        