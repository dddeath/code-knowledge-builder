import argparse
import time


parser = argparse.ArgumentParser()
parser.add_argument("--source")
parser.add_argument("--page", type=int)
parser.add_argument("--output")
parser.add_argument("--schema-version", type=int)
parser.add_argument("--cancel-file")
parser.parse_args()
time.sleep(5)
