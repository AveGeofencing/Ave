# Custom exception classes
class UserServiceError(Exception):
    """Base exception for UserService errors"""

    pass


class UserAlreadyExistsError(UserServiceError):
    """Raised when attempting to create a user that already exists"""

    pass


class UserNotFoundError(UserServiceError):
    """Raised when a user is not found"""

    pass


class TokenError(UserServiceError):
    """Raised when there is an issue with a token"""

    pass


class VerificationCodeError(UserServiceError):
    """Raised when there is an issue with the verification code"""

    pass
