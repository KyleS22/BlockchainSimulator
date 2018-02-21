import threading
import time
import logging


class NodePool:
    def __init__(self):
        # A list of (IP, timestamp) tuples representing the nodes
        # and the last broadcast received
        self.neighbour_list = []

    def check_dead_nodes(self, interval, threshold):
        """
        Loops through the list of (IP, timestamp) tuples to see if any of those nodes are
         not sending broadcasts anymore.
        :param interval: How often to check for dead nodes
        :param threshold: The amount of time between broadcasts before a node is declared dead
        :return: None
        """
        while True:
            time.sleep(interval)

            for node, stamp in self.neighbour_list:
                if time.time() - stamp > threshold:
                    self.neighbour_list.remove((node, stamp))
                    logging.debug("Node %s is dead", node)

    def start(self):
        reaper = threading.Thread(target=self.check_dead_nodes, args=(30, 20,))
        reaper.daemon = True
        reaper.start()
