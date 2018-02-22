import threading
import time
import logging


class NodePool:
    def __init__(self, cleanup_interval, timeout):
        """
        Create a new node pool for tracking other nodes in the network
        :param cleanup_interval: How often to check for dead nodes to cleanup
        :param timeout: The amount of time between broadcasts before a node is declared dead
        """
        self.cleanup_interval = cleanup_interval
        self.timeout = timeout

        # A list of (IP, timestamp) tuples representing the nodes
        # and the last broadcast received
        self.neighbour_list = []

    def cleanup(self, interval, threshold):
        """
        Loops through the list of (IP, timestamp) tuples to see if any of those nodes are
        not sending broadcasts anymore.
        """
        while True:
            time.sleep(interval)

            for node, stamp in self.neighbour_list:
                if time.time() - stamp > threshold:
                    self.neighbour_list.remove((node, stamp))
                    logging.debug("Node %s is dead", node)

    def start(self):
        reaper = threading.Thread(target=self.cleanup)
        reaper.daemon = True
        reaper.start()
