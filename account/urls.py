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
    path('', include(router.urls)),
    path('', include(router2.urls)),
    path('', include(router3.urls)),
    path('', include(router4.urls)),
   
]