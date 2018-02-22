import threading
import time
import logging
import socket


class NodePool:

    def multicast(self, data, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for node in self.pool.keys():
            sock.sendto(data, (node[1], port))

    def __init__(self, node_id, cleanup_interval, timeout):
        """
        Create a new node pool for tracking other nodes in the network
        :param: node_id the identifier used to identify the current node
        :param cleanup_interval: How often to check for dead nodes to cleanup
        :param timeout: The amount of time between broadcasts before a node is declared dead
        """
        self.node_id = node_id
        self.cleanup_interval = cleanup_interval
        self.timeout = timeout

        # A list of (IP, timestamp) tuples representing the nodes
        # and the last broadcast received
        self.pool = dict()
        self.pool_lock = threading.Lock()

    def add(self, node_id, node_address):

        if node_id == self.node_id:
            return

        node = (node_id, node_address)
        with self.pool_lock:
            self.pool[node] = time.time()
            logging.debug("update pool: %s", self.pool)

    def cleanup(self):
        """
        Loops through the list of (IP, timestamp) tuples to see if any of those nodes are
        not sending broadcasts anymore.
        """
        while True:
            time.sleep(self.cleanup_interval)

            cur = time.time()
            with self.pool_lock:
                for key, prev in self.pool.items():
                    if cur - prev > self.timeout:
                        logging.debug("cleanup node: %s", key)
                        self.pool.pop(key)

    def start(self):
        reaper = threading.Thread(target=self.cleanup)
        reaper.daemon = True
        reaper.start()
