from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from assets.views import AssetViewSet, LocationViewSet, LoadCapacityViewSet
from assessments.views import AssessmentViewSet, EquipmentOptionsViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'locations', LocationViewSet)          
router.register(r'load-capacities', LoadCapacityViewSet)  
router.register(r'equipment-options', EquipmentOptionsViewSet, basename='equipment-options')

urlpatterns = [
    path('', views.home, name='home'),
    path('demo/', views.demo, name='demo'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
