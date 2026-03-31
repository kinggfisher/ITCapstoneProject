from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from assets.views import AssetViewSet, LocationViewSet, LoadCapacityViewSet
from assessments.views import AssessmentViewSet
from . import views

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'locations', LocationViewSet)          
router.register(r'load-capacities', LoadCapacityViewSet)  

urlpatterns = [
    path('', views.home, name='home'),
    path('demo/', views.demo, name='demo'),
    path('admin/', admin.site.urls),
    path('api/extract/', views.extract_design_criteria, name='extract'),
    path('api/', include(router.urls)),
]
