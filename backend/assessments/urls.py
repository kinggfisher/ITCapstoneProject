from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet, EquipmentOptionsViewSet

router = DefaultRouter()
router.register(r'assessments', AssessmentViewSet)
router.register(r'equipment-options', EquipmentOptionsViewSet, basename='equipment-options')

urlpatterns = router.urls