class GeofenceServiceException(Exception):
    pass


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
