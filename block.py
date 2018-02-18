from secrets import randbits
from hashlib import sha256
from protos import  block_pb2
import time
import copy


class BlockBuilder:

    def __init__(self, prev_hash, difficulty):
        self.prev_hash = prev_hash
        self.difficulty = difficulty
        self.body = block_pb2.BlockBody()

    def add(self, blob):
        self.body.blobs.append(blob)

    def build(self):
        return Block.block(self.prev_hash, self.difficulty, self.body)


class Block:

    GENESIS_DIFFICULTY = 22
    GENESIS_TIMESTAMP = 1518979622.604106
    GENESIS_NONCE = 0

    def get_difficulty(self):
        return self.header.difficulty

    def get_timestamp(self):
        return self.header.timestamp

    def get_body(self):
        return self.body

    def get_challenge(self):
        return 1 << self.header.difficulty

    def get_nonce(self):
        return self.nonce
    
    @classmethod
    def genesis(cls):
        return cls(b'', cls.GENESIS_DIFFICULTY, block_pb2.BlockBody(), cls.GENESIS_TIMESTAMP, 0, cls.GENESIS_NONCE)

    @classmethod
    def block(cls, prev_hash, difficulty, body):
        return cls(prev_hash, difficulty, body, time.time())

    def __init__(self, prev_hash, difficulty, body, timestamp, entropy=randbits(32), nonce=0):

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

        hashcode = sha256()
        hashcode.update(self.cur_hash)
        hashcode.update(self.prev_hash)
        hashcode.update(str(self.nonce).encode())
        return hashcode.digest()

    def next(self):
        self.nonce += 1

    def is_valid(self):
        hashcode = self.hash()
        for i in range(0, self.header.difficulty):
            byte = hashcode[i // 8]
            if byte & (0x80 >> (i % 8)) != 0:
                return False
        return True
