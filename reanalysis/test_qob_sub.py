import os
import logging
import sys
from cpg_utils.hail_batch import init_batch

def main():

    logging.info("Initializing QoB")

    if 'HAIL_CLOUD' in os.environ.keys():
        print(f"HAIL_CLOUD = {os.environ['HAIL_CLOUD']}")
    else:
        print("HAIL_CLOUD IS NOT SET.")

    os.environ['HAIL_CLOUD'] = 'azure'

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
