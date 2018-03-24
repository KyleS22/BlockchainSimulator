from chain import Chain
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

    def get_resolution_chain(self):
        """
        Returns the binary encoded chain without the block bodies that can be used
        to resolve a node with a lower cost chain that needs to catch up
        :return: The binary encoded resolution chain
        """
        return self.chain.encode(False)

    def __init__(self):

        # the set of blobs that have yet to be validated
        self.pending_blobs_lock = threading.Lock()
        self.pending_blobs = set()

        self.chain_lock = threading.Lock()

        self.chain = Chain()

        # The list of higher cost chains that need to be resolved to catch up the node
        # All floating chains must be the same cost but there may be multiple due to ties
        self.floating_chains = []

        # The highest cost floating chain that is currently being resolved
        self.resolution_chain = None

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

    def receive_block(self, block, chain_cost):
        """
        Receive a block that was mined from a peer node in the network.
        :param block: The block that was mined.
        :param chain_cost: The total cost of the chain that the peer node is working on.
        """
        logging.debug("Receive with cost: %s", chain_cost)
        with self.chain_lock:
            cur = self.chain.blocks[-1]
            if chain_cost > self.chain.get_cost():
                if not block.is_valid(cur.hash()):
                    return self.__add_floating_block(block)

                logging.debug("Added valid remote block")
                block.set_previous_hash(cur.hash())
                self.chain.add(block)
                self.dirty = True

            elif chain_cost == self.chain.get_cost() and block != cur:
                logging.debug('Needs tie resolution')
                return self.__add_floating_block(block)

            return None

    def receive_resolution_chain(self, chain, res_chain):

        with self.chain_lock:
            i = 1
            chain_len = len(self.chain.blocks)
            res_chain_len = len(res_chain.blocks)
            while i < res_chain_len and chain.blocks[i] != res_chain.blocks[i]:

                res_block = res_chain.blocks[i]
                if i < chain_len and self.chain.blocks[i] == res_block:
                    block = self.chain.blocks[i]
                    chain.insert(i, block)
                else:
                    res_block.body = None
                    chain.insert(i, res_block)
                i += 1

        is_valid = chain.is_valid() and chain.get_cost() >= self.chain.get_cost()
        if not is_valid:
            logging.debug("Cur cost: %s New cost: %s", chain.get_cost(), self.chain.get_cost())
            self.floating_chains.remove(chain)
        return is_valid

    def receive_resolution_block(self, block, idx, chain):
        with self.chain_lock:
            cur = chain.blocks[idx - 1]
            if not block.is_valid(cur.hash()):
                return False

            block.set_previous_hash(cur.hash())
            chain.blocks[idx] = block
            return True

    def get_resolution_block_indices(self, chain):
        """
         Gets the list of all blocks in the chain that only have a head. The blocks at
         these indices are missing the binary data for their body.
         :param chain: The chain to find the indices of resolution blocks
         :return: A list of the indices of blocks that are missing their binary body data.
         """
        with self.chain_lock:
            return chain.get_bodiless_indices()

    def get_resolution_block(self, idx):
        with self.chain_lock:
            if idx <= 0 or idx >= len(self.chain.blocks):
                return None
            return self.chain.blocks[idx].encode()

    def receive_complete_chain(self, chain):
        with self.chain_lock:
            self.__receive_complete_chain(chain)

    def __receive_complete_chain(self, chain):
        if chain.get_cost() > self.chain.get_cost():
            self.floating_chains.remove(chain)
            self.chain = chain
            self.dirty = True

            logging.debug("Its longer. Replace the chain.")

        elif chain.get_cost() < self.chain.get_cost():
            logging.debug("Its too short. Throw it out.")
            self.floating_chains.remove(chain)
        else:
            logging.debug("The chains are the same length.")

    def __add_floating_block(self, block):

        for chain in self.floating_chains:
            cur = chain.blocks[-1]
            if block.is_valid(cur.hash()):

                logging.debug("Add to existing floating chain")
                block.set_previous_hash(cur.hash())
                chain.add(block)

                if chain.is_complete():
                    self.__receive_complete_chain(chain)
                return None

            elif block in chain.blocks:
                return None

        logging.debug("Create new floating chain")
        chain = Chain()
        chain.add(block)
        self.floating_chains.append(chain)
        return chain

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
