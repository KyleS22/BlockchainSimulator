import sys
from miner import Miner


def run_project(args):

    node = Miner()
    node.mine()


if __name__ == '__main__':
    run_project(sys.argv)