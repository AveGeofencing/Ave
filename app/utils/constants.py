# Application-wide constants

# Authentication and security
PASSWORD_MIN_LENGTH = 8
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 20

# Email subjects
EMAIL_SUBJECTS = {
    "PASSWORD_RESET": "Password Reset Request ?",
    "PASSWORD_CHANGED": "Password Changed",
    "WELCOME": "Welcome to Ave Geofencing",
    "ATTENDANCE_CONFIRMATION": "Attendance Confirmation",
    "VERIFY": "Ave: Email Verification"
}

# Error messages
ERROR_MESSAGES = {
    "GENERAL_ERROR": "Something went wrong, please contact admin",
    "USER_NOT_FOUND": "User not found",
    "INVALID_CREDENTIALS": "Invalid credentials",
    "SESSION_EXPIRED": "Your session has expired, please log in again",
}
