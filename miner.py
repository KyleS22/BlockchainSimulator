import logging
import math
import threading
import time

from chain import Chain


class Miner:
    """
    The miner that stores the current chain that blocks are being mined for, searches for nonces that allow
    the next block to be added to the chain, and track other chains that may have higher difficulties than
    the current chain that are in the process of chain resolution.
    """

    """
    The difficulty target in number of seconds that the
    difficulty should be adjusted to try and ensure a block
    is mined every DIFFICULTY_TARGET seconds.
    """
    DIFFICULTY_TARGET = 15.0

    def get_resolution_chain(self):
        """
        Returns the binary encoded chain without the block bodies that can be used
        to resolve a node with a lower cost chain that needs to catch up.
        :return: The binary encoded resolution chain.
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
        Starts mining blocks by creating new blocks, searching for valid nonces and adding them to the chain. 
        This method never returns.
        :return: None
        """
        while True:
            while not self.dirty and not cur.is_valid():
                cur.next()

            with self.chain_lock:
                if not self.dirty:
                    self.___add_block(cur)
                    self.__notify_handlers(cur)

                logging.debug("Valid chain: %s Cost: %d", self.chain.is_valid(), self.chain.get_cost())

                difficulty = self.__compute_difficulty()
                with self.pending_blobs_lock:
                    cur = self.chain.next(difficulty, self.pending_blobs)
                self.dirty = False

    def add(self, msg):
        """
        Add a Blob Message to the set of pending blobs to be added to the body of the next block that is created.
        :param msg: The Blob Message as an encoded BlobMessage protocol buffer object consisting of a timestamp
        and binary data.
        :return: None
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
        :return: None
        """
        logging.debug("Receive with cost: %s", chain_cost)
        with self.chain_lock:
            cur = self.chain.blocks[-1]
            if chain_cost > self.chain.get_cost():
                if not block.is_valid(cur.hash()):
                    return self.__add_floating_block(block)

                logging.debug("Added valid remote block")
                block.set_previous_hash(cur.hash())
                self.___add_block(block)
                self.dirty = True

            elif chain_cost == self.chain.get_cost() and block != cur:
                logging.debug('Needs tie resolution')
                return self.__add_floating_block(block)

            return None

    def receive_resolution_chain(self, chain, res_chain):
        """
        Handles a resolution chain from a peer node in the network. This is a chain only consisting of block headers
        with no block data that has been discovered to have a higher cost than the chain that is currently being
        mined. This populates the resolution chain with the block body data for any blocks that match the current
        chain to reduce the amount of data that needs to be sent over the network.
        :param chain: The potentially higher cost chain consisting of a single floating block at the head 
        missing all block's between the genesis block and the head.
        :param res_chain: The chain used to complete the potentially higher cost chain consisting of the block
        headers for all blocks in the chain.
        :return: True if combining the two chains resulted in a valid chain; otherwise, False.
        """
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
        """
        Receive a resolution block from a peer node in the network to add the binary body data to any
        blocks within the higher cost resolution chain that are missing their binary data.
        :param block: The block who's body data should be added to the chain.
        :param idx: The index of the block that the block's body should be added to.
        :param chain: The higher cost chain that is undergoing chain resolution.
        :return: True if the block was successfully added to the chain without invalidating
        the chain; otherwise, False.
        """
        with self.chain_lock:
            prev = chain.blocks[idx - 1]
            if not block.is_valid(prev.hash()):
                return False

            block.set_previous_hash(prev.hash())
            return chain.replace(idx, block)

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
        """
        Get the binary encoded block at the provided index consisting of both its header and binary block
        data to send to a node as a resolution block to help it build the higher cost chain.
        :param idx: The index of the block to be encoded and returned.
        :return: The byte string representation of the block at the provided index or None if the provided index
        was out of the current chain's bounds.
        """
        block = self.get_block(idx)
        if block is None:
            return block
        return block.encode()

    def get_block(self, idx):
        """
        Get the Block at the specified index.
        :param idx: The index of the block to get.
        :return: The block at the specified index or None if the index is out of the current chain's bounds.
        """
        with self.chain_lock:
            if idx < 0 or idx >= len(self.chain.blocks):
                return None
            return self.chain.blocks[idx]

    def remove_floating_chain(self, chain):
        """
        Remove a floating chain, a chain that is in the process of chain resolution to be swapped out, so that it is 
        no longer being tracked by the miner. This should be used if the current chain is now higher cost than
        the floating chain or chain resolution failed.
        :param chain: The floating chain to be removed.
        :return: None
        """
        with self.chain_lock:
            self.floating_chains.remove(chain)

    def receive_complete_chain(self, chain):
        """
        Receive a chain that has completed chain resolution meaning it is ready to swap out the current chain
        due to having all of its block headers and body data and having a valid hash chain.
        :param chain: The completed chain.
        :return: None
        """
        with self.chain_lock:
            self.__receive_complete_chain(chain)

    def __receive_complete_chain(self, chain):
        """
        Receive a chain that has completed chain resolution meaning it is ready to swap out the current chain
        due to having all of its block headers and body data and having a valid hash chain.
        :param chain: The completed chain.
        :return: None
        """
        if chain.get_cost() > self.chain.get_cost():
            self.floating_chains.remove(chain)
            self.chain = chain
            self.dirty = True

            with self.pending_blobs_lock:

                # Add any blobs associated with removed blocks back to pending so they aren't lost
                for block in self.chain.blocks:
                    self.pending_blobs.union(block.get_body().blobs)

                # Remove any pending blobs that have already been included in the new chain
                for block in chain.blocks:
                    self.pending_blobs.difference_update(block.get_body().blobs)

            logging.debug("Its longer. Replace the chain.")

        elif chain.get_cost() < self.chain.get_cost():
            logging.debug("Its too short. Throw it out.")
            self.floating_chains.remove(chain)
        else:
            logging.debug("The chains are the same length.")

    def __add_floating_block(self, block):
        """
        Add a floating block to be tracked by the miner. This is a block from a chain with a greater or equal cost.
        If the floating block can be added to an existing chain undergoing chain resolution then it will be; otherwise,
        a new chain will be created to undergo chain resolution.
        :param block: The floating block to be added.
        :return: None if the floating block was added to an already tracked chain; otherwise, the newly created
        chain to undergo chain resolution.
        """
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
        Add a block to the chain end of the currently mined chain.
        :param block: The block to be added.
        """
        self.chain.add(block)

        with self.pending_blobs_lock:
            self.pending_blobs.difference_update(block.get_body().blobs)

    def __notify_handlers(self, block):
        """
        Notify all handlers that are listening for block mined events that occur
        when the miner succeeds in mining a block and adding it to the current chain.
        :param block:  The block that was mined.
        :return: None
        """
        for handler in self.mine_event:
            handler(block, self.chain.get_cost())

    def __compute_difficulty(self):
        """
        Compute the difficulty for the next block in the chain.
        :return: The difficulty required for the next block to be mined.
        """
        prev = self.chain.blocks[-1]
        if len(self.chain.blocks) == 1:
            return prev.get_difficulty()

        delta = time.time() - self.chain.blocks[-1].get_timestamp()
        difficulty = math.log2(Miner.DIFFICULTY_TARGET / delta) * 0.1 + prev.get_difficulty()

        logging.info("New difficulty: %f Delta: %f", difficulty, delta)

        return int(round(max(difficulty, 1)))
