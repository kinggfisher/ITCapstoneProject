from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from assets.views import AssetViewSet, LocationViewSet, LoadCapacityViewSet
from rest_framework.routers import DefaultRouter
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
    path('api/extract/', views.extract_design_criteria, name='extract'),
    path('api/logout/', views.logout, name='logout'),
    path('api/', include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)