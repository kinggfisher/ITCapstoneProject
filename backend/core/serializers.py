from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class SuperuserTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['is_superuser'] = user.is_superuser
        return token
