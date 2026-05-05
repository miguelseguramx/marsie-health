from django.conf import settings
from django.core.mail import send_mail


def send_onboarding_email(user, token: str) -> None:
    link = f"{settings.FRONTEND_URL.rstrip('/')}/onboarding/{token}"
    greeting = f"Hi {user.first_name}," if user.first_name else "Hi,"
    body = (
        f"{greeting}\n\n"
        "A new lab report is waiting for you on marsie. "
        f"Set your password to view it: {link}\n\n"
        "This link expires in 7 days."
    )
    send_mail(
        subject="Your lab report is ready — set up your account",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
