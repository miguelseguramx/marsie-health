from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.roles import user_role


class MarsieTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["email"] = self.user.email
        data["role"] = user_role(self.user)
        return data


class MeSerializer(serializers.Serializer):
    email = serializers.CharField(source="user.email", read_only=True)
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        # `obj` is the request.user passed in by MeView.
        return user_role(obj)


class OnboardingCompleteSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value
