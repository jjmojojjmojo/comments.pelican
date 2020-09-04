"""
Exceptions
"""

class CommentsError(Exception):
    """
    Base for all comment-plugin related exceptions.
    """
    
class UIDExists(CommentsError):
    """
    Raised when a UID is already in use.
    """

class ParentNotFound(CommentsError):
    """
    Raised when a parent UID is not known
    """
    
class UIDTooManyRetries(CommentsError):
    """
    Raised when a unique UID can't be created after the maximum retries.
    """