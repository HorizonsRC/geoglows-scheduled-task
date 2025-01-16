"""Pull a list of reaches from GeoGLOWS and save to a CSV file."""

import geoglows
import pandas as pd
import logging
import tempfile

# Load the environment variables from the .env file
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# Get the paths to the input and output files from the environment variables (.env file)
reach_file = os.environ["REACH_FILE"]
output_file = os.environ["OUTPUT_FILE"]
backup_dir = os.environ["BACKUP_DIR"]
log_dir = os.environ["LOG_DIR"]

# Get the date that the data was pulled in a nice format for the file names
date = pd.Timestamp.now().strftime("%Y-%m-%d")

# Set up logging
logger = logging.getLogger(__name__)
log_filename = os.path.join(log_dir, f"geoglows_reaches_{date}.log")
file_handler = logging.FileHandler(log_filename)
stream_handler = logging.StreamHandler()
file_fomatter = logging.Formatter("%(asctime)s - %(levelname)s | %(message)s")
file_handler.setFormatter(file_fomatter)
stream_handler.setFormatter(file_fomatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)

# Read the site list with reach numbers from the file.
try:
    reach_df = pd.read_csv(reach_file)
except Exception as e:
    logger.error(f"Error reading file {reach_file}: {e}")
    raise
# Remove any leading or trailing white space from the column names and values
reach_df = reach_df.rename(columns=lambda x: x.strip())
reach_df = reach_df.map(lambda x: x.strip() if isinstance(x, str) else x)

# Drop sites with no reach numbers
reach_df = reach_df.dropna(subset=["GeoglowsReachID"])

# Get the forecast data for each reach. Iterate over reach number and site name pairs
df_list = []
for reach, site_name in reach_df[["GeoglowsReachID", "Sitename"]].values:
    # Catch and log any errors that occur when getting the data
    try:
        data = geoglows.data.forecast(river_id=reach)
        # df comes out as a multiindex with the index a tuple of timestamp and reach_id
        # flatten the index to just the timestamp, turning reach_id into a column
        data["reach_id"] = data.index.get_level_values(1)
        data.index = data.index.get_level_values(0)
        # parse index as datetime, convert from UTC to NZST
        data.index = pd.to_datetime(data.index).tz_convert("etc/gmt-12")
        logger.info(f"Got data for reach {int(reach)} " f"({site_name})")
        df_list.append(data)
    except Exception as e:
        logger.error(f"Error getting data for reach {int(reach)} ({site_name}): {e}")
        continue

# Check if any data was returned
if not df_list:
    logger.error("No data was returned. Aborting.")
    raise ValueError("No data was returned")

# Combine the data into a single DataFrame (no duplicate timestamps)
df = pd.concat(df_list, axis=1, keys=reach_df["Sitename"])

# Construct the backup file name from the date and path
backup_file = os.path.join(backup_dir, f"geoglows_backup_{date}.csv")

# Save the data to a CSV file
try:
    df.to_csv(output_file)
    logger.info("Saved data to " + output_file)
except Exception as e:
    logger.error(f"Output file cannot be saved to {output_file}: {e}")

    logger.info("Attempting to force save the output file.")
    # create a temp filename by adding "_temp" to the end, but before the extension
    temp_file_parts = os.path.splitext(output_file)
    temp_output_file = temp_file_parts[0] + ".temp"
    df.to_csv(temp_output_file)
    # We'll try to replace the locked file in the batch script
try:
    df.to_csv(backup_file)

    logger.info("Saved backup data to " + backup_file)
except Exception as e:
    logger.error(f"Backup file cannot be saved to {backup_file}: {e}")

    logger.info("Attempting to force save the backup file.")
    # create a temp filename by adding "_temp" to the end, but before the extension
    temp_file_parts = os.path.splitext(backup_file)
    temp_backup_file = temp_file_parts[0] + ".temp"
    df.to_csv(temp_backup_file)
    # We'll try to replace the locked file in the batch script
