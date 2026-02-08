"""User email metadata classes"""

from .base import BaseEmail


class WelcomeUserEmail(BaseEmail):
    subject: str = "[Ave] Welcome to Ave"
    template_path: str = "/user_account/welcome_to_ave.html"


class PasswordResetConfirmation(BaseEmail):
    subject: str = "[Ave] Your details have been changed"
    template_path: str = "/user_account/password_reset_confirmation.html"


class UserVerificationEmail(BaseEmail):
    subject: str = "[Ave] Email Verification"
    template_path: str = "/user_account/verification.html"


class PasswordResetEmail(BaseEmail):
    subject: str = "[Ave] Password Reset"
    template_path: str = "/user_account/password_reset.html"
