# Custom exception classes
class UserServiceException(Exception):
    """Base exception for UserService errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)



class UserAlreadyExistsError(UserServiceException):
    """Raised when attempting to create a user that already exists"""

    pass


class UserNotFoundError(UserServiceException):
    """Raised when a user is not found"""

    pass


class TokenError(UserServiceException):
    """Raised when there is an issue with a token"""

    pass


class VerificationCodeError(UserServiceException):
    """Raised when there is an issue with the verification code"""

    pass
