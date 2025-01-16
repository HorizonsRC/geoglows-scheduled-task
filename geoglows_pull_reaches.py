"""Pull a list of reaches from GeoGLOWS and save to a CSV file."""

import geoglows
import pandas as pd
import logging
import tempfile

# Load the environment variables from the .env file
import os
from dotenv import load_dotenv

load_dotenv()

# Get the paths to the input and output files from the environment variables (.env file)
reach_file_path = os.environ["REACH_FILE"]
output_file_path = os.environ["OUTPUT_PATH"]
backup_file_path = os.environ["BACKUP_PATH"]
log_file_path = os.environ["LOG_PATH"]

# Get the date that the data was pulled in a nice format for the file names
date = pd.Timestamp.now().strftime("%Y-%m-%d")

# Set up logging
logger = logging.getLogger(__name__)
log_filename = os.path.join(log_file_path, f"geoglows_reaches_{date}.log")
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
    reach_df = pd.read_csv(reach_file_path)
except Exception as e:
    logger.error(f"Error reading file {reach_file_path}: {e}")
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

# Construct the output file name from the date and path
output_filename = os.path.join(output_file_path, f"geoglows_reaches_latest.csv")
backup_filename = os.path.join(backup_file_path, f"geoglows_reaches_{date}.csv")


# Save the data to a CSV file
# If the file is open, it will be locked and the script will fail
# That's why we save to a temporary, which we can then rename to the final file
temp_output_dir, temp_output_file = tempfile.mkstemp(
    dir=os.path.dirname(output_file_path)
)
temp_backup_dir, temp_backup_file = tempfile.mkstemp(
    dir=os.path.dirname(backup_file_path)
)

try:
    # Write the data to a temporary file
    with os.fdopen(temp_output_dir, "w") as temp_output:
        df.to_csv(temp_output_file, index=False)

    # Replace the temporary file with the final file
    os.replace(temp_output_file, output_filename)
    logger.info("Saved data to " + output_filename)
except Exception as e:
    logger.error(f"File cannot be saved to {output_filename}: {e}")
    if os.path.exists(temp_output_file):
        os.remove(temp_output_file)

try:
    # Write the backup data to a temporary file
    with os.fdopen(temp_backup_dir, "w") as temp_backup:
        df.to_csv(temp_backup_file, index=False)

    # Replace the temporary file with the final file
    os.replace(temp_backup_file, backup_filename)
    logger.info("Saved backup data to " + backup_filename)
except Exception as e:
    logger.error(f"Backup file cannot be saved to {backup_filename}: {e}")
    if os.path.exists(temp_backup_file):
        os.remove(temp_backup_file)
