class HireLoopException(Exception):
    """Base exception for HireLoop"""
    pass

class LinkedInAPIError(HireLoopException):
    pass

class CalendarAPIError(HireLoopException):
    pass

class EmailAPIError(HireLoopException):
    pass

class JobPostingError(HireLoopException):
    pass

class ParsingError(HireLoopException):
    pass
