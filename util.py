import logging


def log_collection(level, msg, col):

    if logging.getLogger().getEffectiveLevel() < level:
        return

    msg += " ["
    for blob in col:
        msg += "\n\t%s" % blob
    if len(col) > 0:
        msg += "\n"
    msg += "]"

    logging.log(level, msg)
