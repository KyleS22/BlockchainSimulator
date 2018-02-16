import sys
from node import Node


def run_project(args):

    node = Node()
    node.mine()


if __name__ == '__main__':
    run_project(sys.argv)