from block import Block, BlockBuilder
import math
import time
import threading

class Miner:

    DIFFICULTY_TARGET = 10.0

    pending_data_lock = threading.Lock()
    pending_data = set()

    chain = []

    def __init__(self):
        genesis = Block.genesis()
        self.chain.append(genesis)

    def mine(self):

        cur = self.__next_block()
        while True:
            while not cur.is_valid():
                cur.next()

            # TODO Add interrupt to stop mining and move to the next block if a block is received from another node
            self.chain.append(cur)

            cur = self.__next_block()

    def add_data(self, data):
        with self.pending_data_lock:
            self.pending_data.add(data)

    def __next_block(self):

        prev = self.chain[-1]
        difficulty = self.__update_difficulty()
        return BlockBuilder(prev.hash(), difficulty).build()

    def __update_difficulty(self):

        prev = self.chain[-1]
        if len(self.chain) == 1:
            return prev.get_difficulty()

        # TODO Add sliding window difficulty recalculation
        delta = time.time() - self.chain[-1].get_timestamp()
        difficulty = math.log2(Miner.DIFFICULTY_TARGET / delta) * 0.1 + prev.get_difficulty()
        print("new difficulty: " + str(difficulty) + " delta: " + str(delta))
        return int(round(max(difficulty, 1)))
