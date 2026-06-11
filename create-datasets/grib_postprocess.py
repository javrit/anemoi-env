#!/usr/bin/env python3
"""
grib_postprocess.py
====================
Post-processing script for SDEdit GRIB files.

Context
-------
SDEdit-generated GRIB files are assumed to contain exactly 3 time steps,
written in files as +3h, +6h and +9h. In the SDEdit framework, these correspond to
perturbed states at +0h, +3h and +6h relative to the analysis date.

To build a dataset compatible with Météo-France's data-driven model (which
uses a 6h time step), we need to reframe the time steps correctly:
  - Keep only +0h and +6h (i.e. drop the intermediate +3h step)
  - Shift all remaining steps by -3h so they are labelled +0h and +6h
  - Rename the output file with date + 1 day to reflect the new reference time

For each GRIB file matching the input glob pattern:
  - Verifies that exactly 3 distinct time steps are present (+3h, +6h, +9h)
  - Removes all messages at the 2nd time step (+6h, index 1 in sorted order)
  - Shifts the remaining steps by -3h and updates validityDate/validityTime accordingly
  - Writes the result to OUTPUT_DIR, renaming the file with date + 1 day

Input filename format : SDEdit_YYYY-MM-DD_preprocessed.grib
Output filename format: SDEdit_YYYY-MM-DD+1_post_processed.grib

Example:
    SDEdit_2024-10-14_0.grib -> SDEdit_2024-10-15_0.grib
"""


import sys
import re
import glob
from pathlib import Path
from datetime import datetime, timedelta


try:
    import eccodes
except ImportError:
    sys.exit("eccodes not found. Install it: pip install eccodes")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

INPUT_GLOB  = "/project/home/p200177/DE_371/avritj/anemoi/samples_grib_to_dataset/not_processed/SDEdit_2024-10-14_*.grib"
OUTPUT_DIR  = Path("/project/home/p200177/DE_371/avritj/anemoi/samples_grib_to_dataset/post_processed_1")

SHIFT_HOURS      = -3     # step shift applied to retained time steps
N_STEPS_EXPECTED = 3      # expected number of distinct steps per file

# ─────────────────────────────────────────────────────────────────────────────


def parse_date_from_filename(path: Path) -> datetime | None:
    """Extract the date from a filename of the form SDEdit_YYYY-MM-DD_*.grib.

    Parameters
    ----------
    path : Path
        Path to the input GRIB file.

    Returns
    -------
    datetime | None
        Parsed date, or None if the pattern is not found.
    """
    match = re.search(r"SDEdit_(\d{4}-\d{2}-\d{2})", path.name)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y-%m-%d")


def build_output_filename(input_path: Path, date: datetime) -> str:
    """Build the output filename by replacing the date with date + 1 day,
    keeping the rest of the filename identical.
 
    Parameters
    ----------
    input_path : Path
        Path to the input GRIB file.
    date : datetime
        Date parsed from the input filename.
 
    Returns
    -------
    str
        Output filename with date + 1 day, same name otherwise.
    """
    old_date = date.strftime("%Y-%m-%d")
    new_date = (date + timedelta(days=1)).strftime("%Y-%m-%d")
    return input_path.name.replace(old_date, new_date)


def grib_validity_datetime(msg) -> datetime:
    
    """Read the validity datetime from a GRIB message.

    Parameters
    ----------
    msg : eccodes message handle
        GRIB message.

    Returns
    -------
    datetime
        Validity datetime of the message.
    """
    vdate = eccodes.codes_get(msg, "validityDate")
    vtime = eccodes.codes_get(msg, "validityTime")
    return datetime.strptime(f"{vdate:08d}{vtime:04d}", "%Y%m%d%H%M")


def get_step(msg) -> int:
    """Read the step value from a GRIB message.

    Parameters
    ----------
    msg : eccodes message handle
        GRIB message.

    Returns
    -------
    int
        Step value in hours.
    """
    step_str = eccodes.codes_get(msg, "stepRange")
    return int(step_str.split("-")[-1])



def inspect_file(path: Path) -> tuple[bool, list[int], int]:
    """Read and validate the time steps present in a GRIB file.

    Parameters
    ----------
    path : Path
        Path to the GRIB file to inspect.

    Returns
    -------
    tuple[bool, list[int], int]
        - ok: whether the file is valid and has the expected number of steps
        - sorted_unique_steps: sorted list of unique steps found
        - total_message_count: total number of GRIB messages in the file
    """
    steps = []
    try:
        with open(path, "rb") as f:
            while True:
                msg = eccodes.codes_grib_new_from_file(f)
                if msg is None:
                    break
                try:
                    steps.append(get_step(msg))
                finally:
                    eccodes.codes_release(msg)
    except Exception as e:
        print(f"    Cannot read file: {e}")
        return False, [], 0

    if not steps:
        print("    Empty file or invalid GRIB.")
        return False, [], 0

    unique_steps = sorted(set(steps))
    n_unique = len(unique_steps)

    print(f"    Steps found        : {unique_steps}  ({len(steps)} messages total)")

    if n_unique != N_STEPS_EXPECTED:
        print(f"    Expected {N_STEPS_EXPECTED} steps, found {n_unique}. Skipping file.")
        return False, [], 0

    drop_step = unique_steps[1]
    kept = [s for s in unique_steps if s != drop_step]
    final = [s + SHIFT_HOURS for s in kept]

    print(f"    Dropping           : step={drop_step}h (2nd time step)")
    print(f"    Keeping            : {kept}")
    print(f"    After shift ({SHIFT_HOURS:+d}h)  : {final}")

    if any(s < 0 for s in final):
        print(f"    Shift would produce negative steps. Skipping file.")
        return False, [], 0

    return True, unique_steps, len(steps)



def process_file(input_path: Path, output_path: Path, drop_step: int) -> bool:
    """Process a GRIB file: drop the 2nd time step and shift remaining steps.

    Parameters
    ----------
    input_path : Path
        Path to the input GRIB file.
    output_path : Path
        Path to the output GRIB file.
    drop_step : int
        Step value (in hours) to remove from the file.

    Returns
    -------
    bool
        True if processing succeeded, False otherwise.
    """
    kept = dropped = errors = 0

    try:
        with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
            while True:
                msg = eccodes.codes_grib_new_from_file(f_in)
                if msg is None:
                    break
                try:
                    step = get_step(msg)
                    if step == drop_step:
                        dropped += 1
                    else:
                        clone = eccodes.codes_clone(msg)
                        try:
                            new_step = step + SHIFT_HOURS

                            old_vdt = grib_validity_datetime(msg)

                            new_vdt = old_vdt + timedelta(hours=SHIFT_HOURS)

                            eccodes.codes_set(clone, "endStep", new_step)
                            eccodes.codes_set(clone, "startStep", new_step)

                            new_ref = new_vdt - timedelta(hours=new_step)
                            eccodes.codes_set(clone, "dataDate", int(new_ref.strftime("%Y%m%d")))
                            eccodes.codes_set(clone, "dataTime", int(new_ref.strftime("%H%M")))

                            eccodes.codes_write(clone, f_out)
                            kept += 1
                        finally:
                            eccodes.codes_release(clone)

                except Exception as e:
                    print(f"    Warning: message skipped: {e}")
                    errors += 1
                finally:
                    eccodes.codes_release(msg)
    except Exception as e:
        print(f"    I/O error: {e}")
        return False

    print(f"    Kept: {kept}  |  Dropped: {dropped}"
          + (f"  |  Warnings: {errors}" if errors else ""))

    if errors > 0:
        return False

    try:
        out_steps = []
        with open(output_path, "rb") as f:
            while True:
                msg = eccodes.codes_grib_new_from_file(f)
                if msg is None:
                    break
                try:
                    out_steps.append(get_step(msg))
                finally:
                    eccodes.codes_release(msg)
        print(f"    Output verification -> {sorted(set(out_steps))} ({len(out_steps)} messages)  OK")
    except Exception as e:
        print(f"    Warning: output verification failed: {e}")

    return kept > 0


def main():
    grib_files = sorted(glob.glob(INPUT_GLOB))

    if not grib_files:
        sys.exit(f"No files found matching pattern: {INPUT_GLOB}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sep = "─" * 64
    print(f"\n{sep}")
    print(f"  GRIB Post-Processing  —  {len(grib_files)} file(s) found")
    print(f"  Pattern    : {INPUT_GLOB}")
    print(f"  Drop       : 2nd time step of each file")
    print(f"  Shift      : {SHIFT_HOURS:+d} h")
    print(f"  Output dir : {OUTPUT_DIR}")
    print(sep)

    ok_count = fail_count = skip_count = 0

    for i, grib_path in enumerate(grib_files, 1):
        input_path = Path(grib_path)
        print(f"\n[{i}/{len(grib_files)}]  {input_path.name}")

        date = parse_date_from_filename(input_path)
        if date is None:
            print("    Cannot parse date from filename. Skipping.")
            skip_count += 1
            continue

        output_name = build_output_filename(input_path, date)
        output_path = OUTPUT_DIR / output_name
        print(f"    Output filename    : {output_name}")

        ok, unique_steps, _ = inspect_file(input_path)
        if not ok:
            skip_count += 1
            continue

        drop_step = unique_steps[1]
        success = process_file(input_path, output_path, drop_step)

        if success:
            size_kb = output_path.stat().st_size / 1024
            print(f"    Saved: {output_path.name}  ({size_kb:.1f} KB)")
            ok_count += 1
        else:
            if output_path.exists():
                output_path.unlink()
                print("    Partial output file removed.")
            fail_count += 1

    print(f"\n{sep}")
    print(f"  SUMMARY")
    print(f"  Success : {ok_count}")
    if skip_count:
        print(f"  Skipped : {skip_count}")
    if fail_count:
        print(f"  Failed  : {fail_count}")
    print(f"{sep}\n")

    if fail_count:
        sys.exit(1)


if __name__ == "__main__":
    main()