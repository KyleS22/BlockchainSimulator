from block import Block, BlockBuilder
from protos import request_pb2
from collections import defaultdict
import math
import time
import threading
import logging
import util


class Miner:

    DIFFICULTY_TARGET = 15.0

    def __init__(self):

        self.pending_blobs_lock = threading.Lock()
        self.pending_blobs = set()

        self.mined_blobs = defaultdict(set)

        self.chain = []
        self.chain_lock = threading.Lock()

        genesis = Block.genesis()
        self.chain.append(genesis)

        # If the block chain has been modified since mining started
        self.dirty = True

    def mine(self):

        while True:
            while not self.dirty and not cur.is_valid():
                cur.next()

            with self.chain_lock:
                if not self.dirty:
                    self.___add_block(cur)

                logging.debug("Valid chain: %s", self.is_valid())

                difficulty = self.__compute_difficulty()
                cur = self.__next_block(difficulty)
                self.dirty = False

    def add(self, msg):
        with self.pending_blobs_lock:
            self.pending_blobs.add(msg)

    def receive_block(self, block, chain_cost):

        with self.chain_lock:

            # only set dirty if chain is modified
            self.dirty = True

    def ___add_block(self, block):

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

    def __next_block(self, difficulty):

        prev = self.chain[-1]
        builder = BlockBuilder(prev.hash(), difficulty)

        with self.pending_blobs_lock:

            debug_msg = "Building block: %d blobs:" % len(self.pending_blobs)
            util.log_collection(logging.DEBUG, debug_msg, self.pending_blobs)

            for blob in self.pending_blobs:
                builder.add(blob)
        return builder.build()

    def __compute_difficulty(self):

        prev = self.chain[-1]
        if len(self.chain) == 1:
            return prev.get_difficulty()

        # TODO Add sliding window difficulty recalculation
        delta = time.time() - self.chain[-1].get_timestamp()
        difficulty = math.log2(Miner.DIFFICULTY_TARGET / delta) * 0.1 + prev.get_difficulty()

        logging.info("New difficulty: %f Delta: %f", difficulty, delta)

        return int(round(max(difficulty, 1)))

    def is_valid(self):

        for i in range(1, len(self.chain)):
            cur = self.chain[i]
            prev = self.chain[i - 1]
            if cur.prev_hash != prev.hash() or not cur.is_valid():
                return False
        return True
