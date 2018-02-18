from secrets import randbits
from hashlib import sha256
from protos import block_pb2
import time
import copy


class BlockBuilder:

    def __init__(self, prev_hash, difficulty):
        """
         Initialize a new block builder for building the next block in the chain.
         :param prev_hash: The hash of the previous block in the chain.
         :param difficulty: The difficulty target in number of 0's in the hash required to mine the block.
         """
        self.prev_hash = prev_hash
        self.difficulty = difficulty
        self.body = block_pb2.BlockBody()

    def add(self, blob):
        """
         Add a blob message to the block's body.                                                            
        :param: blob: The binary data containing the blob's data and the timestamp it was received
            encoded using the BlobMessage protocol buffer.
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
        :return: The integer difficulty in terms of number of leading 0 bits required for the SHA256 hash.
        """
        return self.header.difficulty

    def get_timestamp(self):
        """
        :return: The timestamp the block was created at.
        """
        return self.header.timestamp

    def get_body(self):
        """
        :return: A BlockBody protocol buffer object for the block's body containing the list of encoded 
            BlobMessage objects.
        """
        return self.body

    def get_cost(self):
        """
        :return: The amount of work that had to be put in to mine the block. Each increase in difficulty doubles the
            amount of work that needs to be done.
        """
        return 1 << self.header.difficulty

    def get_nonce(self):
        """
        :return: The current nonce that is changed to try and reach a hash with enough 0 bits to meet the difficulty
            requirement.
        """
        return self.nonce
    
    @classmethod
    def genesis(cls):
        """
        Creates the genesis block which is the first block in the block chain shared by all nodes.
        :return: The genesis block.
        """
        return cls(b'', cls.GENESIS_DIFFICULTY, block_pb2.BlockBody(), cls.GENESIS_TIMESTAMP, 0, cls.GENESIS_NONCE)

    @classmethod
    def block(cls, prev_hash, difficulty, body):
        """
        Creates a new block that can be mined and added to the end of the block chain.
        :param prev_hash: The hash of the previous block in the block chain.
        :param difficulty: The difficulty target in number of 0's in the hash required to mine the block.
        :param body: A BlockBody protocol buffer object for the block's body containing the list of encoded.
        :return: 
        """
        return cls(prev_hash, difficulty, body, time.time())

    def __init__(self, prev_hash, difficulty, body, timestamp, entropy=randbits(32), nonce=0):
        """
        Initialize a new block
        :param prev_hash: The hash of the previous block in the block chain.
        :param difficulty: The difficulty target in number of 0's in the hash required to mine the block.
        :param body: A BlockBody protocol buffer object for the block's body containing the list of encoded.
        :param timestamp: The timestamp the block was created at.
        :param entropy: A secure random number to avoid collisions even if two nodes are mining blocks with
            identical timestamps and block bodies.
        :param nonce: The integer nonce value to start at when mining the block.
        """
        self.nonce = nonce
        self.prev_hash = prev_hash
        self.body = body

        self.header = block_pb2.BlockHeader()
        self.header.entropy = entropy
        self.header.timestamp = timestamp
        self.header.difficulty = difficulty
        self.header.body_hash = sha256(self.body.SerializeToString()).digest()
        self.cur_hash = sha256(self.header.SerializeToString()).digest()

    def hash(self):
        """
        Compute the SHA256 hash of the block.
        :return: A 256 bit bytes object containing the SHA256 hash.
        """
        hashcode = sha256()
        hashcode.update(self.cur_hash)
        hashcode.update(self.prev_hash)
        hashcode.update(str(self.nonce).encode())
        return hashcode.digest()

    def next(self):
        """
        Increments the nonce by one to try and find a nonce that causes
            the hash to satisfy the required difficulty.
        """
        self.nonce += 1

    def is_valid(self):
        """
        Tests whether the block has been mined by computing the SHA256 hash
            and determining if the number of leading 0 bits is greater
            than or equal to the difficulty.
        :return: True if a nonce has been found that satisfies the difficulty, otherwise False.
        """
        hashcode = self.hash()
        for i in range(0, self.header.difficulty):
            byte = hashcode[i // 8]
            # 0x80 = 1000 0000 to test each bit in an individual byte by bit shifting
            if byte & (0x80 >> (i % 8)) != 0:
                return False
        return True
