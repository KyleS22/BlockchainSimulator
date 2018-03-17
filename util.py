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


def convert_int_to_4_bytes(num):
    """
    Convert the given integer into a bytstring representation
    :param num: The number to convert
    :return: The bytestring representation of num
    """
    return (num).to_bytes(4, byteorder='big')


def convert_int_from_4_bytes(bytes):
    """
    Convert a 4 byte bytstring into an integer
    :param bytes: The 4 byte bytestring to convert
    :return: The integer representation of bytes
    """
    return int.from_bytes(bytes, 'big')


