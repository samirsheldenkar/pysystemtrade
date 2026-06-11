from sysdata.data_blob import dataBlob
from sysproduction.data.instruments import diagInstruments
from sysinit.futures.rollcalendars_from_db_prices_to_csv import (
    build_and_write_roll_calendar,
)


def build_all_roll_calendars():
    """
    Generate roll calendars for all instruments using raw contract price data
    """
    data = dataBlob()
    diag_instruments = diagInstruments(data)
    all_instruments = diag_instruments.get_list_of_instruments()

    print(
        f"Found {len(all_instruments)} instruments. Starting roll calendar generation..."
    )

    for instrument_code in all_instruments:
        try:
            print(f"\n--- Processing {instrument_code} ---")
            build_and_write_roll_calendar(
                instrument_code, write=True, check_before_writing=False
            )
            print(f"Successfully generated roll calendar for {instrument_code}")
        except Exception as e:
            print(f"Failed to generate roll calendar for {instrument_code}: {str(e)}")


if __name__ == "__main__":
    input(
        "Will overwrite existing roll calendars for all instruments. Are you sure?! CTL-C to abort"
    )
    build_all_roll_calendars()
