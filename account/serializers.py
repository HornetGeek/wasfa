from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer
from .models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUsers  # Use CustomUsers directly
        fields = ('id', 'email', 'fullName','password', 'created_at', 'fcm_token', "civil_number","Practice_License_Number",'Commercial_number',"role", "profile_picture" ,'title', 'country', 'status','branch')    



class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUsers  # Use CustomUsers directly
        fields = ('id', 'email', 'fullName', 'created_at', 'fcm_token', "civil_number","Practice_License_Number",'Commercial_number',"role" , "blocked","profile_picture", 'title', 'country', 'status','branch')    



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
        if user.blocked:
            raise serializers.ValidationError('This user account is blocked')
        if user.status == 'pending':  # Assuming 'status' is a field in the model
            raise serializers.ValidationError('This user account is still pending approval')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials')

        # Return user object in validated data for token creation
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        serialized_user = UserSerializer(user).data
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': serialized_user,
        }
    

class PatientSerializer(serializers.ModelSerializer):
    prescription_count = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ('id', 'doctorId', 'name', 'idNumber', 'phone_number','created_at','prescription_count')

    def get_prescription_count(self, obj):
        return obj.get_prescription_count()  # Call the method we defined on the Patient model
    
class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'doctorId', 'patientId', 'type', 'created_at']


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = ['id', 'prescriptionId', 'name', 'status']
        

class ConfirmDrugsSerializer(serializers.Serializer):
    prescription_id = serializers.IntegerField()
    drug_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1
    )

    def validate(self, data):
        prescription_id = data.get('prescription_id')
        drug_ids = data.get('drug_ids')

        # Validate if the prescription exists
        if not Prescription.objects.filter(id=prescription_id).exists():
            raise serializers.ValidationError("Prescription does not exist.")

        # Fetch all drugs with the provided IDs
        drugs = Drug.objects.filter(id__in=drug_ids)

        # Check if any of the specified drugs do not exist
        missing_drug_ids = set(drug_ids) - set(drugs.values_list('id', flat=True))
        if missing_drug_ids:
            raise serializers.ValidationError(
                f"Drugs with IDs {missing_drug_ids} do not exist."
            )

        # Validate if all drugs belong to the specified prescription
        invalid_drugs = drugs.exclude(prescriptionId_id=prescription_id)
        if invalid_drugs.exists():
            raise serializers.ValidationError("Some drugs do not belong to the given prescription.")

        return data

    def update_status(self):
        drug_ids = self.validated_data['drug_ids']
        # Update only the valid drugs
        Drug.objects.filter(id__in=drug_ids).update(status='confirmed')
