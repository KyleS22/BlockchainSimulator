from chain import Chain
from block import Block
import math
import time
import threading
import logging


class Miner:

    """
    The difficulty target in number of seconds that the
    difficulty should be adjusted to try and ensure a block
    is mined every DIFFICULTY_TARGET seconds.
    """
    DIFFICULTY_TARGET = 15.0

    def __init__(self):

        # the set of blobs that have yet to be validated
        self.pending_blobs_lock = threading.Lock()
        self.pending_blobs = set()

        self.chain_lock = threading.Lock()

        self.chain = Chain()
        self.mine_event = []

        # If the block chain has been modified since mining started
        self.dirty = True

    def mine(self):
        """
        Starts mining blocks by creating new blocks, searching for valid nonces
        and adding them to the chain. This method never returns.
        """
        while True:
            while not self.dirty and not cur.is_valid():
                cur.next()

            with self.chain_lock:
                if not self.dirty:
                    self.___add_block(cur)

                logging.debug("Valid chain: %s Cost: %d", self.chain.is_valid(), self.chain.get_cost())

                difficulty = self.__compute_difficulty()
                with self.pending_blobs_lock:
                    cur = self.chain.next(difficulty, self.pending_blobs)
                self.dirty = False

    def add(self, msg):
        """
        Add a Blob Message to the set of pending blobs to be
        added to the body of the next block that is created.
        :param msg: The Blob Message as a BlobMessage protocol buffer object.
        """
        with self.pending_blobs_lock:
            if msg in self.pending_blobs:
                return False
            self.pending_blobs.add(msg)
        return True

    def receive_block(self, block_data, chain_cost):
        """
        Receive a block that was mined from a peer node in the network.
        :param block_data: The block that was mined.
        :param chain_cost: The total cost of the chain that the peer node is working on.
        """
        with self.chain_lock:
            cur = self.chain.blocks[-1]
            if chain_cost > self.chain.get_cost():
                block = Block.decode(cur.hash(), block_data)
                if block.is_valid():
                    logging.debug("ADDED VALID REMOTE BLOCK!!!")
                    self.chain.add(block)
                    self.dirty = True
                else:
                    logging.debug("Found a larger chain, todo fetch it")
            elif chain_cost < self.chain.get_cost():
                logging.debug("Found a smaller chain, todo tell it its too short")
            else:
                block = Block.decode(b'', block_data)
                if block == cur:
                    logging.debug('received a duplicate block')
                else:
                    logging.debug('received a block thats the same length, tie breaker stuff')

    def ___add_block(self, block):
        """
        Add a block to the chain. This involves removing all of the blobs in its
        body from the pending blobs set.
        :param block: The block to be added.
        """
        self.chain.add(block)

        for handler in self.mine_event:
            handler(block, self.chain.get_cost())

        with self.pending_blobs_lock:
            self.pending_blobs.difference_update(block.get_body().blobs)

    def __compute_difficulty(self):
        """
        Compute the difficulty for the next block in the chain.
        :return: The difficulty required for the next block to be mined.
        """
        prev = self.chain.blocks[-1]
        if len(self.chain.blocks) == 1:
            return prev.get_difficulty()

        # TODO Add sliding window difficulty recalculation
        delta = time.time() - self.chain.blocks[-1].get_timestamp()
        difficulty = math.log2(Miner.DIFFICULTY_TARGET / delta) * 0.1 + prev.get_difficulty()

        logging.info("New difficulty: %f Delta: %f", difficulty, delta)

        return int(round(max(difficulty, 1)))
