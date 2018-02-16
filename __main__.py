import sys
from block import BlockBuilder, Block


def run_project(args):

    cur = Block.genesis()
    while True:

        while not cur.is_valid():
            cur.next()
        cur = BlockBuilder(cur.hash(), cur.get_difficulty()).build()


if __name__ == '__main__':
    run_project(sys.argv)