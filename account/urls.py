from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import *
from .views import *

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)

router2 = DefaultRouter()
router2.register(r'patients', PatientViewSet)


router3 = DefaultRouter()
router3.register(r'prescription', PrescriptionViewSet)

router4 = DefaultRouter()
router4.register(r'drugs', DrugViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='token_obtain_pair'),
    path('login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('filter/users/', UserListView.as_view({'get': 'list'}), name='user-list'),
    path('confirm-drugs/', ConfirmDrugsView.as_view(), name='confirm-drugs'),
    path('users/<int:user_id>/confirm-status/', confirm_user_status, name='confirm_user_status'),
    path('users/<int:user_id>/refused-status/', refuse_user_status, name='refused_user_status'),
    path('users/pharmacy/pending/', list_pending_pharmacy_users, name='list_pending_pharmacy_users'),
    path('users/pharmacy/blocked/', list_blocked_pharmacy_users, name='list_blocked_pharmacy_users'),
    path('users/pending/', list_pending_users, name='list_pending_users'),
    path('users/pharmacy/search/', search_sort_pharmacy_users, name='search_sort_pharmacy_users'),
    path('', include(router.urls)),
    path('', include(router2.urls)),
    path('', include(router3.urls)),
    path('', include(router4.urls)),
   
]