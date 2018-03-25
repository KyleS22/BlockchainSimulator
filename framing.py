"""
The length of the integer header used to frame TCP messages in a TCP stream.
"""
LENGTH_HEADER_SIZE = 4


def convert_int_to_4_bytes(num):
    """
    Convert the given integer into a byte string representation.
    :param num: The number to convert.
    :return: The byte string representation of num.
    """
    return (num).to_bytes(4, byteorder='big')


def convert_int_from_4_bytes(bytes):
    """
    Convert a 4 byte byte string into an integer.
    :param bytes: The 4 byte byte string to convert.
    :return: The integer representation of bytes.
    """
    return int.from_bytes(bytes, 'big')


def frame_segment(data):
    """
    Adds length framing to a binary message to allow the message to be sent in a TCP stream and pieced back together 
    from multiple TCP segments.
    :param data: The data to have length framing appended.
    :return: A framed byte string that can be sent.
    """
    req_length = convert_int_to_4_bytes(len(data))
    return req_length[:] + data[:]


def receive_framed_segment(sock):
    """
    Receive a length framed segment from the TCP stream on the provided socket.
    :param sock: The already connected TCP stream socket to receive a framed message on.
    :return: The framed segment's binary data or an empty byte string if the socket was closed between framed segments.
    :except: A RuntimeError is thrown if the socket connection is broken while in the process of 
    receiving a framed message.
    """

    len_header = b''
    bytes_received = 0

    # Check for closed socket connection in case there isn't a next message
    segment = sock.recv(LENGTH_HEADER_SIZE - bytes_received)
    if segment == b'':
        return segment

    len_header += segment
    bytes_received = bytes_received + len(segment)

    # Receive the rest of the length header if it wasn't in the the first TCP segment
    while bytes_received < LENGTH_HEADER_SIZE:
        segment = sock.recv(LENGTH_HEADER_SIZE - bytes_received)
        if segment == b'':
            raise RuntimeError("socket connection broken")
        len_header += segment
        bytes_received = bytes_received + len(segment)

    msg = b''
    msg_len = convert_int_from_4_bytes(len_header[:LENGTH_HEADER_SIZE])
    bytes_received = 0

    # Receive the message body
    while bytes_received < msg_len:
        segment = sock.recv(msg_len - bytes_received)
        if segment == b'':
            raise RuntimeError("socket connection broken")
        msg += segment
        bytes_received = bytes_received + len(segment)

    return msg
