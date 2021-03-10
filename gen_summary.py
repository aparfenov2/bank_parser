import sys
from utils import read_transactions
import argparse, logging


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('csvdir')
    parser.add_argument('--out', default="summary.json")
    return parser

def main(self, args):
    logging.basicConfig(level=logging.INFO)
    Main(args).main()

class Main:
    def  __init__(self, args):
        self.args = args
        self.logger = logging.getLogger(self._class.__name__)

    def main(self):
        pass

if __name__ == "__main__":
    main(make_parser().parse_args(sys.argv))
