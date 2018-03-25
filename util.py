import logging


def log_collection(level, msg, col):
    """
    A logging utility function to log collections with each item on a new line.
    :param level: The messages log level.
    :param msg: The message that is displayed as prefix before the collection.
    :param col: The collection to be logged.
    """
    if logging.getLogger().getEffectiveLevel() < level:
        return

    msg += " ["
    for blob in col:
        msg += "\n\t%s" % blob
    if len(col) > 0:
        msg += "\n"
    msg += "]"

    logging.log(level, msg)
