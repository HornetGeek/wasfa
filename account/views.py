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
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q


class PatientPagination(PageNumberPagination):
    page_size = 10  # Number of results per page
    page_size_query_param = 'page_size'  # Allow clients to customize the page size
    max_page_size = 100  # Limit on the maximum number of results per page
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,  # Total items
            'total_pages': self.page.paginator.num_pages,  # Total pages
            'current_page': self.page.number,  # Current page number
            'next': self.get_next_link(),  # Next page URL
            'previous': self.get_previous_link(),  # Previous page URL
            'results': data  # Paginated results
        })

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
                fcm_token=user_data.get('fcm_token', ''),
                role=user_data.get('role', 'doctor'),
                branch= user_data.get('branch', ''),
                civil_number = user_data.get("civil_number",""),
                Commercial_number = user_data.get('Commercial_number',""),
                title = user_data.get('title','')
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
    filter_backends = [SearchFilter]
    search_fields = [
        'email',                 # Search by email
        'fullName',              # Search by full name
        'civil_number',          # Search by civil number
        'Practice_License_Number',  # Search by practice license number
        'Commercial_number',     # Search by commercial number
        'fcm_token',             # Search by FCM token
        'role',                  # Search by role
    ]
    pagination_class = PatientPagination

class UserListView(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserListSerializer
    pagination_class = PatientPagination  # Use the custom pagination class

    def get_queryset(self):
        # Get query parameters
        role = self.request.query_params.get('role', None)
        search_query = self.request.query_params.get('search', '')
        sort_by = self.request.query_params.get('sort_by', 'fullName')  # Default sort field
        sort_order = self.request.query_params.get('sort_order', 'asc')  # Default sort order

        # Mapping of valid sort fields to model fields
        sort_field_mapping = {
            'email': 'email',
            'fullName': 'fullName',
            'Commercial_number': 'Commercial_number',
            'civil_number': 'civil_number',
            'created_at': 'created_at',
        }

        # Validate the sort field
        if sort_by not in sort_field_mapping:
            raise ValueError(f"Invalid sort field. Valid options are: {', '.join(sort_field_mapping.keys())}.")

        # Get the actual model field name
        sort_by_field = sort_field_mapping[sort_by]

        # Adjust sort_by for descending order
        if sort_order == 'desc':
            sort_by_field = f"-{sort_by_field}"

        # Base queryset: exclude blocked users
        queryset = CustomUsers.objects.filter(blocked=False)

        # Apply role filter if specified
        if role:
            queryset = queryset.filter(role=role)

        # Apply search filter if specified
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(civil_number__icontains=search_query) |
                Q(Commercial_number__icontains=search_query) |
                Q(Practice_License_Number__icontains=search_query)
            )

        # Apply sorting
        queryset = queryset.order_by(sort_by_field)

        return queryset
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            # Apply pagination
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = self.get_serializer(paginated_queryset, many=True)

            return paginator.get_paginated_response(serializer.data)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [SearchFilter]  # Retain search functionality
    search_fields = ['idNumber', 'name']
    pagination_class = PatientPagination

    def get_queryset(self):
        queryset = Patient.objects.all()

        # Get query parameters for sorting
        sort_by = self.request.query_params.get('sort_by', 'idNumber')  # Default sorting field
        sort_order = self.request.query_params.get('sort_order', 'asc')  # Default sorting order

        # Validate sort_by field
        valid_sort_fields = ['idNumber', 'name', 'created_at']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort field. Valid options are: {', '.join(valid_sort_fields)}.")

        # Apply sorting order
        if sort_order == 'desc':
            sort_by = f"-{sort_by}"

        # Apply ordering
        queryset = queryset.order_by(sort_by)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-doctor')
    def get_patients_by_doctor(self, request):
        doctor_id = request.query_params.get('doctorId')
        if not doctor_id:
            return Response({"error": "doctorId parameter is required"}, status=400)

        queryset = self.get_queryset().filter(doctorId=doctor_id)
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-id-number')
    def get_patients_by_id_number(self, request):
        id_number = request.query_params.get('idNumber')
        if not id_number:
            return Response({"error": "idNumber parameter is required"}, status=400)

        queryset = self.get_queryset().filter(idNumber=id_number)
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer


    @action(detail=False, methods=['get'], url_path='by-patient')
    def get_prescriptions_by_patient(self, request):
        patient_id = request.query_params.get('patientId')
        if not patient_id:
            return Response({"error": "patientId parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        prescriptions = Prescription.objects.filter(patientId=patient_id)
        if not prescriptions.exists():
            return Response({"detail": "No prescriptions found for this patient ID."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Drug ViewSet
class DrugViewSet(viewsets.ModelViewSet):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer

    @action(detail=False, methods=['get'], url_path='by-prescription')
    def get_drugs_by_prescription(self, request):
        prescription_id = request.query_params.get('prescriptionId')
        if not prescription_id:
            return Response({"error": "prescriptionId parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        drugs = Drug.objects.filter(prescriptionId=prescription_id)
        if not drugs.exists():
            return Response({"detail": "No drugs found for this prescription ID."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(drugs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ConfirmDrugsView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ConfirmDrugsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update_status()
            return Response({"message": "Drugs confirmed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['PATCH'])
def confirm_user_status(request, user_id):
    try:
        # Fetch the user
        user = CustomUsers.objects.get(id=user_id)
        
        # Update the status to 'confirmed'
        user.status = 'confirmed'
        user.save()
        
        return Response({"message": "User status updated to confirmed."}, status=status.HTTP_200_OK)
    except CustomUsers.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PATCH'])
def refuse_user_status(request, user_id):
    try:
        # Fetch the user
        user = CustomUsers.objects.get(id=user_id)

        # Update the status to 'refused'
        user.status = 'refused'
        user.save()

        return Response({"message": "User status updated to refused."}, status=status.HTTP_200_OK)
    except CustomUsers.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_pending_pharmacy_users(request):
    try:
        # Get query parameters for search and sorting
        search_query = request.query_params.get('search', '')  # Default to empty string if not provided
        sort_by = request.query_params.get('sort_by', 'fullName')  # Default to sorting by 'fullName'
        sort_order = request.query_params.get('sort_order', 'asc')  # Default to ascending order

        # Validate sort_by parameter to ensure it's one of the valid fields
        valid_sort_fields = ['fullName', 'email', 'created_at', 'civil_number']
        if sort_by not in valid_sort_fields:
            return Response(
                {"error": f"Invalid sort field. Valid options are {', '.join(valid_sort_fields)}."},
                status=400
            )

        # Handle sorting order
        if sort_order == 'desc':
            sort_by = f"-{sort_by}"

        # Filter users with role 'pharmacy' and status 'pending', apply search query if provided
        filters = Q(role='pharmacy', status='pending')
        if search_query:
            filters &= (
                Q(email__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(civil_number__icontains=search_query) |
                Q(Practice_License_Number__icontains=search_query) |
                Q(Commercial_number__icontains=search_query)
            )

        # Apply filters and sorting
        users = CustomUsers.objects.filter(filters).order_by(sort_by)

        # Apply pagination
        paginator = PatientPagination()
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(paginated_users, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(['GET'])
def list_blocked_pharmacy_users(request):
    try:
        # Get query parameters for search and sorting
        search_query = request.query_params.get('search', '')  # Default to empty string if not provided
        sort_by = request.query_params.get('sort_by', 'fullName')  # Default to sorting by 'fullName'
        sort_order = request.query_params.get('sort_order', 'asc')  # Default to ascending order

        # Validate sort_by parameter to ensure it's one of the valid fields
        valid_sort_fields = ['fullName', 'email', 'created_at', 'civil_number']
        if sort_by not in valid_sort_fields:
            return Response(
                {"error": f"Invalid sort field. Valid options are {', '.join(valid_sort_fields)}."},
                status=400
            )

        # Handle sorting order
        if sort_order == 'desc':
            sort_by = f"-{sort_by}"

        # Filter users with role 'pharmacy' and blocked=True, apply search query if provided
        filters = Q(role='pharmacy', blocked=True)
        if search_query:
            filters &= (
                Q(email__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(civil_number__icontains=search_query) |
                Q(Practice_License_Number__icontains=search_query) |
                Q(Commercial_number__icontains=search_query)
            )

        # Apply filters and sorting
        users = CustomUsers.objects.filter(filters).order_by(sort_by)

        # Apply pagination
        paginator = PatientPagination()
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(paginated_users, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)
    
@api_view(['GET'])
def list_pending_users(request):
    try:
        # Get query parameters for search and sorting
        search_query = request.query_params.get('search', '')  # Default to empty string if not provided
        sort_by = request.query_params.get('sort_by', 'fullName')  # Default to sorting by 'fullName'
        sort_order = request.query_params.get('sort_order', 'asc')  # Default to ascending order

        # Validate sort_by parameter to ensure it's one of the valid fields
        valid_sort_fields = ['fullName', 'created_at', 'email', 'civil_number']
        if sort_by not in valid_sort_fields:
            return Response(
                {"error": f"Invalid sort field. Valid options are {', '.join(valid_sort_fields)}."},
                status=400
            )

        # Handle sorting order
        if sort_order == 'desc':
            sort_by = f"-{sort_by}"

        # Filter users with status 'pending' and apply search query (if provided)
        filters = Q(status='pending')
        if search_query:
            filters &= (
                Q(email__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(civil_number__icontains=search_query) |
                Q(Practice_License_Number__icontains=search_query) |
                Q(Commercial_number__icontains=search_query)
            )

        # Apply filters and sorting
        users = CustomUsers.objects.filter(filters).order_by(sort_by)

        # Apply pagination
        paginator = PatientPagination()
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(paginated_users, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(['GET'])
def search_sort_pharmacy_users(request):
    try:
        # Get query parameters for search and sorting
        search_query = request.query_params.get('search', '')  # Default to empty string if not provided
        sort_by = request.query_params.get('sort_by', 'fullName')  # Default to sorting by 'fullName'
        sort_order = request.query_params.get('sort_order', 'asc')  # Default to ascending order

        # Validate sort_by parameter to ensure it's either 'fullName' or 'created_at'
        if sort_by not in ['fullName', 'created_at']:
            return Response({"error": "Invalid sort field. Valid options are 'fullName' or 'created_at'."}, status=400)

        # Handle sorting order
        if sort_order == 'desc':
            sort_by = f"-{sort_by}"

        # Filter users by 'pharmacy' role and apply search query (if provided)
        filters = Q(role='pharmacy')
        if search_query:
            filters &= (Q(fullName__icontains=search_query) | Q(email__icontains=search_query))

        # Apply filters and sorting
        users = CustomUsers.objects.filter(filters).order_by(sort_by)

        # Serialize the data
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)