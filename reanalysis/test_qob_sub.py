import logging
import sys
from cpg_utils.hail_batch import init_batch

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
