import copy
import logging
import time
from hashlib import sha256
from secrets import randbits

from google.protobuf import message

from protos import block_pb2, request_pb2


class BlockBuilder:
    """
    The block builder for creating a new block. The allows binary data to be added to
    the block body while the block is being built. Once the block is built, the block body
    can no longer have binary objects added to it.
    """

    def __init__(self, prev_hash, difficulty):
        """
         Initialize a new block builder for building the next block in the chain.
         :param prev_hash: The hash of the previous block in the chain.
         :param difficulty: The difficulty target in number of 0's in the hash required to mine the block.
         :return: None
         """
        self.prev_hash = prev_hash
        self.difficulty = difficulty
        self.body = block_pb2.BlockBody()

    def add(self, blob):
        """
         Add a blob message to the block's body.                                                            
        :param: blob: The binary data containing the blob's data and the timestamp it was received
            encoded using the BlobMessage protocol buffer.
        :return: None
        """
        self.body.blobs.append(blob)

    def build(self):
        """
        Build a new block with the previous block's hash, the difficulty, and
            a copy of the blob messages in the block body.
        :return: A new block that can be mined to add it to the chain.
        """
        return Block.block(self.prev_hash, self.difficulty, copy.deepcopy(self.body))


class Block:
    """
    This class models a block within the block chain. It contains the binary data
    that is stored in the block and the header data which contains the data required
    to make the block's hash fit with the previous block in the chain.
    """

    """
    The number of leading 0's required for the SHA256 hash of the genesis block.
    """
    GENESIS_DIFFICULTY = 22

    """
    The timestamp of the genesis block. This may be any timestamp but a timestamp
    closer to the actual time will increase the stability of the difficulty adjustment
    algorithm for the first few blocks.
    """
    GENESIS_TIMESTAMP = 1518979622.604106

    """
    The starting nonce for genesis block. This should be updated to ensure the genesis
    hash meets the required difficulty if the difficulty or timestamp are changed.
    """
    GENESIS_NONCE = 1078537

    def get_difficulty(self):
        """
        Get the difficulty of the block in terms of how much work was put in to mining it. A higher difficulty
        corresponds to requiring more leading 0's in the SHA256 hash.
        :return: The integer difficulty in terms of number of leading 0 bits required for the SHA256 hash.
        """
        return self.header.difficulty

    def get_timestamp(self):
        """
        Get the timestamp the block was created at.
        :return: The timestamp the block was created at.
        """
        return self.header.timestamp

    def get_body(self):
        """
        Get the block's body as a BlockBody protocol buffer which contains a collection of serialized
        binary BlobMessage protocol buffers.
        :return: A BlockBody protocol buffer object for the block's body containing the list of encoded.
        BlobMessage objects.
        """
        return self.body

    def has_body(self):
        """
        Determine if the block has its body data or only a head.
        :return: Returns True if the block has its body data; otherwise, False is returned.
        """
        return self.body is not None

    def set_body(self, body):
        """
        Set the block's body data using a BlockBody protocol buffer. This can only be used if the
        hash of the new body is the same as the body hash in the block header. This allows the body
        to be added to a block that was transferred without its body during chain resolution.
        :param body: The BlockBody protocol buffer to be set as the block's body that must have the
        same hash as the header's body hash.
        :return: None
        """
        if self.header.body_hash != sha256(body.SerializeToString()).digest():
            logging.error("Error: Set body called with data that doesn't match the body hash.")
            return
        self.body = body

    def get_cost(self):
        """
        Get the amount of work that was required to mine the block. This differs from difficulty because costs can
        be compared linearly where as difficulty cannot.
        :return: The amount of work that had to be put in to mine the block. Each increase in difficulty doubles the
        amount of work that needs to be done.
        """
        return 1 << self.header.difficulty

    def get_nonce(self):
        """
        Get the block's nonce which is the value that is changed to try and find a SHA256 hash of the block with
        enough leading 0's to match the difficulty.
        :return: The current nonce that is changed to try and reach a hash with enough 0 bits to meet the difficulty
        requirement.
        """
        return self.nonce

    def set_previous_hash(self, hash):
        self.prev_hash = hash

    @classmethod
    def genesis(cls):
        """
        Creates the genesis block which is the first block in the block chain shared by all nodes.
        :return: The genesis block.
        """
        return cls(b'', cls.GENESIS_DIFFICULTY, block_pb2.BlockBody(), cls.GENESIS_TIMESTAMP, 0, cls.GENESIS_NONCE)

    @classmethod
    def decode(cls, data, has_body=True):
        """
        Decode a block from an encoded Block protocol buffer.
        :param data: The encoded block.
        :param has_body: True if the block has its body data; otherwise, false
        :return: The decoded block.
        :except: If decoding fails then a DecodeError is thrown.
        """
        block_data = block_pb2.Block()
        block_data.ParseFromString(data)

        if has_body:
            body_hash = None
        else:
            body_hash = block_data.header.body_hash

        return cls(block_data.prev_hash,
                   block_data.header.difficulty,
                   block_data.body,
                   block_data.header.timestamp,
                   block_data.header.entropy,
                   block_data.nonce,
                   body_hash)

    @classmethod
    def block(cls, prev_hash, difficulty, body):
        """
        Creates a new block that can be mined and added to the end of the block chain.
        :param prev_hash: The hash of the previous block in the block chain.
        :param difficulty: The difficulty target in number of 0's in the hash required to mine the block.
        :param body: A BlockBody protocol buffer object for the block's body containing the list of encoded.
        :return: The newly created block.
        """
        return cls(prev_hash, difficulty, body, time.time())

    def __init__(self, prev_hash, difficulty, body, timestamp, entropy=randbits(32), nonce=0, body_hash=None):
        """
        Initialize a new block
        :param prev_hash: The hash of the previous block in the block chain.
        :param difficulty: The difficulty target in number of 0's in the hash required to mine the block.
        :param body: A BlockBody protocol buffer object for the block's body containing the list of encoded.
        :param timestamp: The timestamp the block was created at.
        :param entropy: A secure random number to avoid collisions even if two nodes are mining blocks with
            identical timestamps and block bodies.
        :param nonce: The integer nonce value to start at when mining the block.
        :param body_hash: The body hash to be set in the header that is only used if the provided body is None.
        """
        self.nonce = nonce
        self.prev_hash = prev_hash
        self.body = body

        self.header = block_pb2.BlockHeader()
        self.header.entropy = entropy
        self.header.timestamp = timestamp
        self.header.difficulty = difficulty
        if body_hash is not None:
            self.header.body_hash = body_hash
        else:
            self.header.body_hash = sha256(self.body.SerializeToString()).digest()
        self.cur_hash = sha256(self.header.SerializeToString()).digest()

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.cur_hash == other.cur_hash and self.nonce == other.nonce
        return False

    def hash(self, prev_hash=None):
        """
        Compute the SHA256 hash of the block.
        :return: A 256 bit byte string containing the SHA256 hash.
        """
        hashcode = sha256()
        hashcode.update(self.cur_hash)
        if prev_hash is None:
            hashcode.update(self.prev_hash)
        else:
            hashcode.update(prev_hash)
        hashcode.update(str(self.nonce).encode())
        return hashcode.digest()

    def next(self):
        """
        Increments the nonce by one to try and find a nonce that causes the hash to satisfy the required difficulty.
        """
        self.nonce += 1

    def encode(self, include_body=True):
        """
        Encode the block into a binary representation that can be sent across the network.
        :param include_body: Indicate whether to encode the data in the block's body.
        :return: The binary encoded block.
        """
        block = block_pb2.Block()
        block.nonce = self.nonce
        block.prev_hash = self.prev_hash
        block.header.CopyFrom(self.header)
        if include_body:
            block.body.CopyFrom(self.body)
        return block.SerializeToString()

    def is_valid(self, prev_hash=None):
        """
        Tests whether the block has been mined by computing the SHA256 hash and determining if the number of leading 
        0 bits is greater than or equal to the difficulty.
        :param prev_hash: The hash of the previous block in the chain
        :return: True if a nonce has been found that satisfies the difficulty; otherwise, False.
        """
        hashcode = self.hash(prev_hash)
        for i in range(0, self.header.difficulty):
            byte = hashcode[i // 8]
            # 0x80 = 1000 0000 to test each bit in an individual byte by bit shifting
            if byte & (0x80 >> (i % 8)) != 0:
                return False
        return True

    def to_ascii(self):
        """
        Creates an ASCII representation of the data stored within the block's body. If any of the BlobMessage's
        within the body cannot be decoded they are omitted.
        :return: The ASCII encoded representation of the block's body
        """

        if len(self.body.blobs) == 0:
            return "{}\n"
        lines = "{\n"
        for blob in self.body.blobs:
            msg = request_pb2.BlobMessage()
            try:
                msg.ParseFromString(blob)
            except message.DecodeError:
                logging.error("Error: Failed to convert blob to ASCII.")
                continue
            lines += "\t" + "timestamp: " + str(msg.timestamp) + " blob: " + msg.blob.decode()
        return lines + "}\n"
