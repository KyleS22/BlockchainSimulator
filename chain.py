import logging
import util
from block import BlockBuilder, Block
from collections import defaultdict
from protos import request_pb2


class Chain:

    def __init__(self):

        # the dictionary of mined blobs to allow a blob to be looked up using its hash to find which block it is in
        self.mined_blobs = defaultdict(set)

        self.blocks = []
        genesis = Block.genesis()
        self.blocks.append(genesis)

        self.cost = 0

    def add(self, block):
        """
        Add a block to the chain.
        :param block: The block to be added.
        """
        debug_msg = "Add block to chain with nonce: %d blobs:" % block.get_nonce()
        util.log_collection(logging.DEBUG, debug_msg, block.get_body().blobs)

        block_num = len(self.blocks)
        for idx, blob in enumerate(block.get_body().blobs):
            msg = request_pb2.BlobMessage()
            msg.ParseFromString(blob)
            self.mined_blobs[hash(msg.blob)].add((block_num, idx))

        self.blocks.append(block)

    def next(self, difficulty, blobs):
        """
        Build the next block to try to add to the chain.
        :param difficulty: The difficulty required for the next block to be mined.
        :param blobs: The blobs to be added to the body of the next block.
        """
        prev = self.blocks[-1]
        builder = BlockBuilder(prev.hash(), difficulty)

        debug_msg = "Building block: %d blobs:" % len(blobs)
        util.log_collection(logging.DEBUG, debug_msg, blobs)

        for blob in blobs:
            builder.add(blob)

        return builder.build()

    def is_valid(self):
        """
        Tests whether the chain is valid by computing and verifying the chain of hashes
        :return: True if the chain is valid, otherwise False
        """
        for i in range(1, len(self.blocks)):
            cur = self.blocks[i]
            prev = self.blocks[i - 1]
            if cur.prev_hash != prev.hash() or not cur.is_valid():
                return False
        return True
