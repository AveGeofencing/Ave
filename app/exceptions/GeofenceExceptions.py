class GeofenceServiceException(Exception):

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GeofenceAlreadyExistException(GeofenceServiceException):
    pass


class InvalidDurationException(GeofenceServiceException):
    pass


class GeofenceStatusException(GeofenceServiceException):
    pass


class AlreadyRecordedAttendanceException(GeofenceServiceException):
    pass


class UserNotInGeofenceException(GeofenceServiceException):
    pass
