import logging
import socket
import threading
import time


class NodePool:
    """
    The node pool used to keep track of and send messages to other peers in the network using a soft state
    approach to track nodes that are alive.
    """

    def multicast(self, data, port):
        """
        Psuedo-UDP multi-casting by sending the provided data to all known peers in the pool
        on the provided port. True multi-casting cannot be used due to lack of Docker support.
        :param data: The data to be sent to all known peers in the pool.
        :param port: The port to send the data to on the peers.
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with self.pool_lock:
            for node in self.pool.keys():
                sock.sendto(data, (node[1], port))

    def __init__(self, node_id, cleanup_interval, timeout):
        """
        Create a new node pool for tracking other nodes in the network.
        :param: node_id: The unique identifier used to identify the current node.
        :param cleanup_interval: How often to check for dead nodes to cleanup.
        :param timeout: The amount of time between broadcasts before a node is declared dead.
        :return: None
        """
        self.node_id = node_id
        self.cleanup_interval = cleanup_interval
        self.timeout = timeout

        # A list of (IP, timestamp) tuples representing the nodes
        # and the last broadcast received
        self.pool = dict()
        self.pool_lock = threading.Lock()

    def add(self, node_id, node_address):
        """
        Add a new peer node to the node pool.
        :param node_id: The unique identifier of the node to be added.
        :param node_address: The address to communicate with the node.
        :return: None
        """
        if node_id == self.node_id:
            return

        node = (node_id, node_address)
        with self.pool_lock:
            self.pool[node] = time.time()
            logging.debug("update pool: %s", self.pool)

    def cleanup(self):
        """
        Cleanup the node pool using a soft state approach to remove all nodes that for which a discovery message
        has not been received for longer than the node pool's timeout period.
        :return: None
        """
        """
        Loops through the list of (IP, timestamp) tuples to see if any of those nodes are
        not sending broadcasts anymore.
        """
        while True:
            time.sleep(self.cleanup_interval)

            cur = time.time()
            with self.pool_lock:
                for key, prev in list(self.pool.items()):
                    if cur - prev > self.timeout:
                        logging.debug("cleanup node: %s", key)
                        self.pool.pop(key)

    def start(self):
        """
        Start the cleanup thread to periodically check for nodes that should be removed from the pool due
        to not receiving any discovery messages from them.
        :return: None
        """
        reaper = threading.Thread(target=self.cleanup)
        reaper.daemon = True
        reaper.start()
