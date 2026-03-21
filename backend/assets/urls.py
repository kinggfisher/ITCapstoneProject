from rest_framework.routers import DefaultRouter
from .views import AssetViewSet

router = DefaultRouter()
router.register(r'assets', AssetViewSet)

urlpatterns = router.urls