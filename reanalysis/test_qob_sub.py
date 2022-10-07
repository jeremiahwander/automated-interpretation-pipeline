from typing import Any
import logging
import sys
from argparse import ArgumentParser

import hail as hl
from peddy import Ped

from cloudpathlib import AnyPath

from cpg_utils import to_path
from cpg_utils.hail_batch import init_batch, output_path

from reanalysis.utils import read_json_from_path


def main():

    logging.info("Initializing QoB")

    # initiate Hail with defined driver spec.
    init_batch(driver_cores=8, driver_memory='highmem')



if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stderr,
    )

    main()
