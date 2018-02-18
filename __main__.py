import sys
from node import Node
import logging


logging.basicConfig(level=logging.DEBUG)


def main(args):
    node = Node()
    node.run()


if __name__ == '__main__':
    main(sys.argv)