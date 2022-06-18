from datetime import datetime as dt

LOGGER_NAME = "tagbase_server"


def tz_aware(datetime):
    """
    Convenience function to determine whether a datetime
    has been localized or not. If it has, tzinfo and utcoffset
    information will be present.
    :param datetime: A datetime to check for localization.
    :rtype: boolean
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return False
    elif dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return True
