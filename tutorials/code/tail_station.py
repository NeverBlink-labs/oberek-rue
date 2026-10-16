# Print every new OBEREK reading as it arrives. Read-only, no credentials.
import io, time
from datetime import datetime, timedelta, timezone

import boto3, pandas as pd
from botocore import UNSIGNED
from botocore.config import Config

FOLDER = "raw/iot/southwest/csv"  # change this line to follow another source (see the table below)

s3 = boto3.client("s3", endpoint_url="https://oberek.neverblink.eu/s3", region_name="us-east-1",
                  config=Config(signature_version=UNSIGNED))
start = datetime.now(timezone.utc) - timedelta(minutes=15)  # begin with the last 15 minutes
cursor = f"{FOLDER}/{start:%Y-%m-%d}/data_{start:%H_%M_%S}.csv"

while True:
    prefix = f"{FOLDER}/{datetime.now(timezone.utc):%Y-%m-%d}/"
    page = s3.list_objects_v2(Bucket="oberek-bucket", Prefix=prefix, StartAfter=max(cursor, prefix))
    for obj in page.get("Contents", []):
        body = s3.get_object(Bucket="oberek-bucket", Key=obj["Key"])["Body"].read()
        rows = pd.read_csv(io.BytesIO(body))
        print(rows[["timestamp", "sensor", "feature", "value"]].to_string(index=False, header=False))
        cursor = obj["Key"]
    time.sleep(60)
