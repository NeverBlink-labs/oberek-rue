"""Follow one OBEREK water-quality station in near real time and plot it live.

The dashboard shows one point per day. The public bucket gets a new file for
every sensor message (about once a minute at SouthWest). This script backfills
the last few hours, then checks for new files every minute and redraws a plot.

Read-only: it only lists and downloads public objects. No credentials needed.

    pip install boto3 pandas matplotlib
    python follow_station.py --station southwest --hours 6
"""
import argparse
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import boto3
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from botocore import UNSIGNED
from botocore.config import Config

ENDPOINT = "https://oberek.neverblink.eu/s3"
BUCKET = "oberek-bucket"

# Which measurements to plot: feature name in the CSV -> panel title.
PANELS = {
    "qudt_qk:Acidity": "pH",
    "bufr4_b13:083": "Dissolved oxygen (mg/L)",
    "s4watr:Turbidity": "Turbidity (NTU)",
}

s3 = boto3.client("s3", endpoint_url=ENDPOINT, region_name="us-east-1",
                  config=Config(signature_version=UNSIGNED, max_pool_connections=16))


def day_prefix(station, day):
    return f"raw/iot/{station}/csv/{day:%Y-%m-%d}/"


def list_new_keys(station, cursor):
    """All CSV keys after `cursor`, walking day folders up to today (UTC).

    Keys look like raw/iot/<station>/csv/2026-09-30/data_11_22_02.csv, so they
    sort by time and S3's StartAfter gives us "everything newer than this".
    """
    day = datetime.strptime(cursor.split("/")[4], "%Y-%m-%d").date()
    today = datetime.now(timezone.utc).date()
    keys = []
    while day <= today:
        args = {"Bucket": BUCKET, "Prefix": day_prefix(station, day), "StartAfter": cursor}
        for page in s3.get_paginator("list_objects_v2").paginate(**args):
            keys += [obj["Key"] for obj in page.get("Contents", [])]
        day += timedelta(days=1)
    return keys


def read_csv(key):
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    return pd.read_csv(io.BytesIO(body), parse_dates=["timestamp"])


def fetch(keys):
    if not keys:
        return pd.DataFrame()
    with ThreadPoolExecutor(16) as pool:
        return pd.concat(pool.map(read_csv, keys), ignore_index=True)


def draw(fig, axes, data, station):
    for ax, (feature, title) in zip(axes, PANELS.items()):
        ax.clear()
        rows = data[data.feature == feature].dropna(subset=["value"])
        ax.plot(rows.timestamp, rows.value, color="#2a7c5e", lw=1.4, marker=".", ms=3)
        ax.set_title(title, loc="left", fontsize=10)
        if rows.empty:
            ax.text(0.5, 0.5, "no readings", transform=ax.transAxes, ha="center", color="grey")
        ax.grid(alpha=0.3)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    latest = data.timestamp.max()
    fig.suptitle(f"OBEREK · {station} station · latest reading {latest:%Y-%m-%d %H:%M} UTC", fontsize=11)


def follow(station, hours, interval, once=False, out=None):
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    cursor = day_prefix(station, start) + f"data_{start:%H_%M_%S}.csv"
    data = pd.DataFrame()
    fig, axes = plt.subplots(len(PANELS), 1, figsize=(9, 7), sharex=True)
    while True:
        keys = list_new_keys(station, cursor)
        if keys:
            cursor = keys[-1]
            data = pd.concat([data, fetch(keys)], ignore_index=True)
            data = data[data.timestamp >= data.timestamp.max() - timedelta(hours=hours)]
            print(f"{datetime.now(timezone.utc):%H:%M:%S} +{len(keys)} files, "
                  f"latest reading {data.timestamp.max():%H:%M:%S} UTC")
            draw(fig, axes, data, station)
            if out:
                fig.savefig(out, dpi=120, bbox_inches="tight")
        if once:
            return data
        plt.pause(interval)  # redraws the window while we wait


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--station", default="southwest", choices=["southwest", "north", "south"],
                   help="south currently sends simulated data")
    p.add_argument("--hours", type=float, default=6, help="how much history to backfill and keep on screen")
    p.add_argument("--interval", type=int, default=60, help="seconds between checks (please keep >= 60)")
    p.add_argument("--once", action="store_true", help="backfill, save the plot and exit")
    p.add_argument("--out", help="also save the plot to this PNG after every update")
    a = p.parse_args()
    follow(a.station, a.hours, max(a.interval, 60), once=a.once, out=a.out)
