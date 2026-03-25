from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, LocationViewSet, LoadCapacityViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'load-capacities', LoadCapacityViewSet)

urlpatterns = router.urls