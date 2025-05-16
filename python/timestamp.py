#!/usr/bin/env python3
    
import datetime
import argparse
import time

def main():
    parser = argparse.ArgumentParser(
        description="Display current Unix timestamp or convert a given Unix timestamp to readable UTC and GMT+8 time.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    parser.add_argument(
        "timestamp_input",
        type=str,
        nargs="?",
        help=(
            "Optional Unix timestamp.\n"
            "Can be in seconds (e.g., 1609459200 or 1609459200.123)\n"
            "or milliseconds (e.g., 1609459200123)."
        )
    )

    args = parser.parse_args()

    if args.timestamp_input is None:
        # If no argument is provided, output current Unix timestamps
        current_ts_seconds = time.time()
        current_ts_milliseconds = int(current_ts_seconds * 1000)
        print(f"Current Unix Timestamp (seconds): {current_ts_seconds}")
        print(f"Current Unix Timestamp (milliseconds): {current_ts_milliseconds}")
    else:
        input_str = args.timestamp_input
        timestamp_in_seconds = 0.0
        original_unit = "seconds" # Assume seconds by default

        try:
            # Determine if input is likely seconds or milliseconds
            if '.' in input_str:
                # Has a decimal, so it's seconds with fractional part
                timestamp_in_seconds = float(input_str)
                original_unit = "seconds"
            else:
                # No decimal, could be integer seconds or milliseconds
                try:
                    # Attempt to convert to integer to check its magnitude/length
                    # A typical millisecond timestamp (e.g., 13 digits) is much larger than a second timestamp (e.g., 10 digits)
                    # and longer.
                    # Using length as a primary heuristic for whole numbers.
                    if len(input_str) > 11: # Heuristic: 10-11 digits for seconds, 13+ for ms
                        timestamp_in_seconds = int(input_str) / 1000.0
                        original_unit = "milliseconds"
                    else:
                        timestamp_in_seconds = float(input_str) # Treat as seconds
                        original_unit = "seconds"
                except ValueError:
                    # If it's not an integer and has no decimal, it might be a float string like "1e9"
                    timestamp_in_seconds = float(input_str)
                    original_unit = "seconds"


            print(f"Input Unix Timestamp ({original_unit}): {input_str}")
            print(f"Interpreted as seconds: {timestamp_in_seconds}")

            # Datetime format string including milliseconds
            datetime_format = "%Y-%m-%d %H:%M:%S.%f %Z"

            # Convert to UTC
            # The fromtimestamp method expects seconds
            dt_utc = datetime.datetime.fromtimestamp(timestamp_in_seconds, tz=datetime.timezone.utc)
            utc_readable = dt_utc.strftime(datetime_format)
            print(f"UTC Time         : {utc_readable}")

            # Convert to GMT+8 (East Asia Standard Time)
            tz_gmt8 = datetime.timezone(datetime.timedelta(hours=8), name="GMT+8")
            # Option 1: Convert directly from timestamp with target timezone
            # dt_gmt8 = datetime.datetime.fromtimestamp(timestamp_in_seconds, tz=tz_gmt8)

            # Option 2: Convert from the UTC datetime object (more common if you already have UTC)
            dt_gmt8 = dt_utc.astimezone(tz_gmt8)
            gmt8_readable = dt_gmt8.strftime(datetime_format)
            print(f"GMT+8 Time       : {gmt8_readable}")

        except ValueError:
            print(f"Error: Invalid timestamp format '{input_str}'. Please provide a valid number.")
        except OverflowError:
            print(f"Error: The provided timestamp '{input_str}' is out of the representable range for dates.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
