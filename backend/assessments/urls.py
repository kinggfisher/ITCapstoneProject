from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet

router = DefaultRouter()
router.register(r'assessments', AssessmentViewSet)

urlpatterns = router.urls