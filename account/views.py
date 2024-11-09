from django.shortcuts import render
import jwt

from rest_framework.permissions import BasePermission
from wasfa import settings
from .models import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from .serializers import *
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from .serializers import *
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import PatientSerializer
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics


class PatientPagination(PageNumberPagination):
    page_size = 10  # Number of results per page
    page_size_query_param = 'page_size'  # Allow clients to customize the page size
    max_page_size = 100  # Limit on the maximum number of results per page


class RegisterView(APIView):
    http_method_names = ['post']
    permission_classes = [BasePermission]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data

            user = CustomUsers.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                fullName=user_data.get('fullName', ''),
                fcm_token=user_data.get('fcm_token', '')
            )
            return Response({"message": "Account created successfully"}, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class EmailTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomTokenObtainSerializer(data=request.data)
        if serializer.is_valid():
            # Return the token data
            return Response(serializer.create(serializer.validated_data), status=status.HTTP_200_OK)

        # Handle errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUsers.objects.all()
    serializer_class = UserListSerializer


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [SearchFilter]
    search_fields = ['idNumber']
    pagination_class = PatientPagination

    @action(detail=False, methods=['get'], url_path='by-doctor')
    def get_patients_by_doctor(self, request):
        doctor_id = request.query_params.get('doctorId')
        if not doctor_id:
            return Response({"error": "doctorId parameter is required"}, status=400)
        
        patients = Patient.objects.filter(doctorId=doctor_id)
        serializer = self.get_serializer(patients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-id-number')
    def get_patients_by_id_number(self, request):
        id_number = request.query_params.get('idNumber')
        if not id_number:
            return Response({"error": "idNumber parameter is required"}, status=400)

        patients = Patient.objects.filter(idNumber=id_number)
        serializer = self.get_serializer(patients, many=True)
        return Response(serializer.data)
    

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer

# Drug ViewSet
class DrugViewSet(viewsets.ModelViewSet):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer