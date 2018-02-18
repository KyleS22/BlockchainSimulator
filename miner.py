from block import Block, BlockBuilder
from protos import request_pb2
from collections import defaultdict
import math
import time
import threading
import logging
import util


class Miner:

    DIFFICULTY_TARGET = 10.0

    def __init__(self):

        self.pending_blobs_lock = threading.Lock()
        self.pending_blobs = set()

        self.mined_blobs = defaultdict(set)

        self.chain = []
        self.chain_lock = threading.Lock()

        genesis = Block.genesis()
        self.chain.append(genesis)

    def mine(self):

        cur = self.__next_block()
        while True:
            while not cur.is_valid():
                cur.next()

            # TODO Add interrupt to stop mining and move to the next block if a block is received from another node
            with self.chain_lock:
                self.__add_block(cur)
                cur = self.__next_block()

    def add(self, msg):
        with self.pending_blobs_lock:
            self.pending_blobs.add(msg)

    def __add_block(self, block):

        debug_msg = "Add block to chain with nonce: %d blobs:" % block.get_nonce()
        util.log_collection(logging.DEBUG, debug_msg, block.get_body().blobs)

        block_num = len(self.chain)
        for idx, blob in enumerate(block.get_body().blobs):

            msg = request_pb2.BlobMessage()
            msg.ParseFromString(blob)
            self.mined_blobs[hash(msg.blob)].add((block_num, idx))

        self.chain.append(block)

        with self.pending_blobs_lock:
            self.pending_blobs.difference_update(block.get_body().blobs)

    def __next_block(self):

        prev = self.chain[-1]
        difficulty = self.__update_difficulty()
        builder = BlockBuilder(prev.hash(), difficulty)

        with self.pending_blobs_lock:

            debug_msg = "Building block: %d blobs:" % len(self.pending_blobs)
            util.log_collection(logging.DEBUG, debug_msg, self.pending_blobs)

            for blob in self.pending_blobs:
                builder.add(blob)
        return builder.build()

    def __update_difficulty(self):

        prev = self.chain[-1]
        if len(self.chain) == 1:
            return prev.get_difficulty()

        # TODO Add sliding window difficulty recalculation
        delta = time.time() - self.chain[-1].get_timestamp()
        difficulty = math.log2(Miner.DIFFICULTY_TARGET / delta) * 0.1 + prev.get_difficulty()

        logging.info("New difficulty: %f Delta: %f", difficulty, delta)

        return int(round(max(difficulty, 1)))
