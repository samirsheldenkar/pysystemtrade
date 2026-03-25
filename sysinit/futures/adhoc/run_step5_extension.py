from sysdata.data_blob import dataBlob
from sysproduction.update_multiple_adjusted_prices import update_multiple_adjusted_prices_for_instrument
from sysproduction.data.prices import diagPrices
import time

def main():
    start_time = time.time()
    with dataBlob(log_name="Consolidation-Update") as data:
        diag = diagPrices(data)
        instruments = sorted(diag.get_list_of_instruments_in_multiple_prices())
        
        failed = []
        for i, code in enumerate(instruments):
            print(f"[{i+1}/{len(instruments)}] Updating {code} ...", end=" ", flush=True)
            try:
                # This function updates both multiple and adjusted prices using the new raw prices and extended roll calendar
                # that were generated in Steps 1, 2, 3, and 4.
                update_multiple_adjusted_prices_for_instrument(code, data)
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
                failed.append((code, str(e)))
        
        print(f"\nExtending multiple & adjusted prices complete in {time.time() - start_time:.2f}s")
        print(f"{len(failed)} failures.")
        if failed:
            for code, err in failed:
                print(f"  {code}: {err}")

if __name__ == "__main__":
    main()
