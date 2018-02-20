
class NodePool:
	
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

		for node, stamp in self.udp_server.neighbour_list:
			if time.time() - stamp > threshold:
				self.udp_server.neighbour_list.remove((node, stamp))
				logging.debug("Node %s is dead", node)
				
	