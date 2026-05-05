from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import OnboardingToken
from apps.accounts.roles import user_role
from apps.accounts.serializers import (
    MarsieTokenObtainPairSerializer,
    OnboardingCompleteSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = MarsieTokenObtainPairSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(
            {
                "email": request.user.email,
                "role": user_role(request.user),
            }
        )


class OnboardingCompleteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OnboardingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = (
            OnboardingToken.objects
            .select_related("user", "report")
            .filter(token=serializer.validated_data["token"])
            .first()
        )
        if token is None:
            return Response(
                {"detail": "Invalid or unknown onboarding token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if token.consumed_at is not None:
            return Response(
                {"detail": "This onboarding link has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if token.expires_at <= timezone.now():
            return Response(
                {"detail": "This onboarding link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = token.user
            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=["password"])
            token.consumed_at = timezone.now()
            token.save(update_fields=["consumed_at"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": user.email,
                "role": user_role(user),
                "report_id": str(token.report_id) if token.report_id else None,
            }
        )
