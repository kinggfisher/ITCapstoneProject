from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from assets.views import AssetViewSet, LocationViewSet, LoadCapacityViewSet
from assessments.views import AssessmentViewSet

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'locations', LocationViewSet)          
router.register(r'load-capacities', LoadCapacityViewSet)  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
