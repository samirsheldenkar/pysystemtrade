from sysdata.data_blob import dataBlob
from sysproduction.data.instruments import diagInstruments
from sysinit.futures.seed_price_data_from_IB import seed_price_data_from_IB
import time
import logging
import os
from datetime import datetime


def setup_logging():
    """
    Set up logging configuration with both file and console handlers
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"seed_ib_prices_{timestamp}.log")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    return log_file


def seed_all_instruments_from_IB():
    """
    Seeds price data from Interactive Brokers for all instruments in the system

    This script will:
    1. Get a list of all instruments from the system
    2. For each instrument:
       - Get price data for all available contracts
       - Store both hourly and daily data
       - Write merged prices
    3. Includes error handling and logging
    """
    # Setup logging
    log_file = setup_logging()
    logging.info(f"Log file created at: {log_file}")

    data = dataBlob()
    diag_instruments = diagInstruments(data)

    # Get list of all instruments
    all_instruments = diag_instruments.get_list_of_instruments()

    logging.info(f"Found {len(all_instruments)} instruments to process")
    logging.info(f"Instruments to process: {', '.join(all_instruments)}")

    success_count = 0
    error_count = 0
    error_instruments = []

    for instrument_code in all_instruments:
        try:
            logging.info(f"\nProcessing instrument: {instrument_code}")
            start_time = time.time()

            seed_price_data_from_IB(instrument_code)

            end_time = time.time()
            duration = end_time - start_time
            logging.info(
                f"Successfully processed {instrument_code} in {duration:.2f} seconds"
            )
            success_count += 1

            # Add a small delay to avoid overwhelming IB
            time.sleep(1)

        except Exception as e:
            error_msg = f"Error processing {instrument_code}: {str(e)}"
            logging.error(error_msg, exc_info=True)  # Include full traceback
            error_count += 1
            error_instruments.append((instrument_code, str(e)))
            continue

    # Log summary
    logging.info("\n=== Processing Summary ===")
    logging.info(f"Total instruments processed: {len(all_instruments)}")
    logging.info(f"Successfully processed: {success_count}")
    logging.info(f"Failed to process: {error_count}")

    if error_count > 0:
        logging.warning("\nFailed instruments:")
        for instrument, error in error_instruments:
            logging.warning(f"{instrument}: {error}")


if __name__ == "__main__":
    logging.info("Starting to seed price data for all instruments from IB")
    seed_all_instruments_from_IB()
    logging.info("Completed seeding price data for all instruments")
