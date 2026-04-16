from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet, EquipmentOptionsViewSet, AssessmentHistoryViewSet

router = DefaultRouter()
router.register(r'assessments', AssessmentViewSet)
router.register(r'equipment-options', EquipmentOptionsViewSet, basename='equipment-options')
router.register(r'assessment-history', AssessmentHistoryViewSet, basename='assessment-history')

urlpatterns = router.urls