---
layout: tutorial
title: Follow a sensor station in real time
permalink: /tutorials/live-data/
lead: Connect to the public OBEREK data bucket, pick up each new reading as soon as it is stored, and build your own apps on top of it.
description: Short guide for developers and AI agents to stream OBEREK sensor data from the public S3-compatible bucket and reuse it in their own applications.
audience: software developers, AI agents
time: 5 min read · Python
---

## Why not just use the dashboard?

The dashboard shows **one point per day**: the daily average of each measurement over the last 30 days.
Behind it, every message a sensor station sends is stored as its own file, in several formats, about once a minute.
The files are public and machine-readable, and every source uses the same layout. You can plug them into your own
app, database or alerting without asking anyone for access.

<div class="table-scroll" markdown="1">

| | Dashboard series | Raw sensor files |
|---|---|---|
| How often | 1 value per day, last 30 days | every message: about every minute at SouthWest, every 10 min at North |
| Where | `<location>/raw/iot/<feature>/latest.json` | `raw/iot/<station>/<format>/<YYYY-MM-DD>/data_HH_mm_ss.<ext>` |
| Formats | JSON | CSV, JSON, TTL (RDF), Jelly (binary RDF) |
| Contents | one feature per file | every measurement from that message |

</div>

## What you connect to

- **Endpoint:** `https://oberek.neverblink.eu/s3`. This is an S3-compatible gateway (path-style addressing).
- **Bucket:** `oberek-bucket`
- **Access:** public and read-only. You don't need credentials; uploads and deletions are refused.
- **Stations:** `southwest` (Sèquia de Rizarbe) and `north` (Sèquia de Ravisanxo). A third station, `south`, currently sends simulated data, so leave it out of anything real. The KEI results for the South and Global locations are calculated from it too.
- **How the files are made:** every ingestion and calculation pipeline is open source, in [NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code). If you want to know exactly how a column was produced, the pipeline that writes it is there.

Each CSV file holds one sensor message, with one row per measurement:

```text
timestamp,device,sensor,feature,statistic_type,unit,value
2026-10-16T16:33:06.806Z,nbi:Estacion_SouthWest,nbi:Estacion_SouthWest-ph,qudt_qk:Acidity,,unit:PH,7.6
2026-10-16T16:33:06.806Z,nbi:Estacion_SouthWest,nbi:Estacion_SouthWest-oxygen,bufr4_b13:083,,unit:MilliGM-PER-L,13.33
2026-10-16T16:33:06.806Z,nbi:Estacion_SouthWest,nbi:Estacion_SouthWest-ec,s4mari:WaterConductivity,,unit:MicroS-PER-CentiM,1611.0
…
```

The `feature` and `unit` columns use short RDF names (for example, `qudt_qk:Acidity` is pH, `bufr4_b13:083` is
dissolved oxygen, from the WMO code tables, and `unit:NTU` is nephelometric turbidity units). The full list with plain names is on the dashboard's
[Help page, under Data Export](https://oberek.neverblink.eu/help). Every name is also defined, in English, Spanish and Valencian, in the
[OBEREK ontology](https://github.com/NeverBlink-labs/oberek-code/blob/main/model/oberek-ontology-init/oberek_ontology.ttl) and
[metadata](https://github.com/NeverBlink-labs/oberek-code/blob/main/model/oberek-metadata-init/oberek_metadata.ttl).

## What you install

Only well-known, open-source Python libraries. There is no OBEREK-specific package, and the scripts are short enough to read before you run them.

- [**boto3**](https://pypi.org/project/boto3/): Amazon's official Python library for S3. It also works with other S3-compatible storage, like this gateway. We use it only to list and download files.
- [**pandas**](https://pandas.pydata.org/): the standard Python library for working with tables. It reads the CSV files.
- [**matplotlib**](https://matplotlib.org/): the standard Python plotting library. You only need it for the live chart in step 3.

## 1. Look before you code (30 seconds)

File names sort by time, so S3's `start-after` gives you "everything newer than this file".
List what arrived at SouthWest today after 11:00 UTC, then download one file:

```bash
BASE=https://oberek.neverblink.eu/s3/oberek-bucket
DAY=$(date -u +%F)
curl -s "$BASE/?list-type=2&prefix=raw/iot/southwest/csv/$DAY/&start-after=raw/iot/southwest/csv/$DAY/data_11_00_00.csv" \
  | grep -o '<Key>[^<]*' | sed 's/<Key>//'

curl -s "$BASE/raw/iot/southwest/csv/$DAY/data_11_00_06.csv"   # use a key from the list above
```

With the AWS CLI it's the same, plus `--no-sign-request`:

```bash
aws --endpoint-url https://oberek.neverblink.eu/s3 --no-sign-request \
    s3 ls s3://oberek-bucket/raw/iot/southwest/csv/$(date -u +%F)/ | tail -3
```

## 2. Attach to the stream (about 20 lines)

This is the whole idea. Remember the last file you saw, ask for anything after it once a minute, and read the new files.

```python
{% include_relative code/tail_station.py %}
```

Run it with `pip install boto3 pandas` and then `python tail_station.py`. Each new message prints a few lines.
To keep it short, this version doesn't pick up files written in the last minute before midnight UTC.
The script in step 3 handles that too.

**Same code, other data.** Every OBEREK source is stored the same way, so changing `FOLDER` is enough to follow another one.
The weather folder is called `avamet` because the station belongs to the AVAMET network; the data itself comes from Fundació Assut:

<div class="table-scroll" markdown="1">

| `FOLDER` | What arrives | How often |
|---|---|---|
| `raw/iot/southwest/csv`, `raw/iot/north/csv` | water sensors: pH, oxygen, turbidity, conductivity, salinity, temperature | about every minute / every 10 min |
| `raw/avamet/estell/csv` | weather from the Tancat de l'Estell station (Fundació Assut, part of the AVAMET network): temperature, humidity, rain, wind, pressure, sunlight, evapotranspiration, leaf wetness | every few minutes |
| `raw/copernicus/csv` | Copernicus Sentinel-2 satellite: chlorophyll-a, phycocyanin, Secchi depth, vegetation and water indices, per location | once a day |
| `raw/csv-water/csv` | lagoon water level and flow through the golas, from the six gauging stations of the Júcar river authority (CHJ) | twice a day (CHJ updates the data once a day) |
| `raw/polls/csv` | community poll answers, from the dashboard and from paper forms | when someone answers |
| `keis/kei-1/csv`, `keis/kei-2/csv`, `keis/kei-3/csv` | the indicator levels and scores OBEREK calculates, per location | every 15 min |
| `keis/pyricularia-risk-index/csv` | rice blast risk index | every hour |

</div>

## 3. Plot it live

[`follow_station.py`]({{ '/tutorials/code/follow_station.py' | relative_url }}) does the same thing with a backfill and a live chart.
It loads the last few hours, draws pH, dissolved oxygen and turbidity, and redraws the chart every minute when new files arrive.

```bash
pip install boto3 pandas matplotlib
python follow_station.py --station southwest --hours 6    # opens a window that keeps updating
python follow_station.py --station north --hours 24 --once --out north.png   # one picture, then exit
```

<figure class="shot">
  <div class="shot-frame"><img src="{{ '/assets/tutorials/img/live-data/live.gif' | relative_url }}" alt="Animated chart of pH, dissolved oxygen and turbidity at the SouthWest station, gaining new points each minute" width="{{ site.data.live_capture.width }}" height="{{ site.data.live_capture.height }}"></div>
  <figcaption>A real run of <code>follow_station.py</code>, recorded on {{ site.data.live_capture.captured }}: {{ site.data.live_capture.polls }} checks, one per minute, shown sped up.</figcaption>
</figure>

<figure class="shot">
  <div class="shot-frame"><img src="{{ '/assets/tutorials/img/live-data/southwest-6h.png' | relative_url }}" alt="Six hours of per-minute pH, dissolved oxygen and turbidity readings at the SouthWest station" loading="lazy"></div>
  <figcaption>Six hours at SouthWest on 16 October 2026: about 280 messages. The dashboard turns this whole day into a single point. The flat turbidity line at about 1,000 NTU is the sensor stuck at the top of its range, not water that stayed exactly the same.</figcaption>
</figure>

<details markdown="1">
<summary>Show the full script</summary>

```python
{% include_relative code/follow_station.py %}
```

</details>

## 4. Build on it

The loop in step 2 is all an app needs. Replace the `print(...)` with whatever your app does. For example:

- **Keep your own history** at full resolution, in any database. With SQLite it's two lines:

  ```python
  import sqlite3
  db = sqlite3.connect("oberek.db")   # once, before the loop
  rows.to_sql("readings", db, if_exists="append", index=False)   # instead of print(...)
  ```

- **Send alerts.** Check a value in the loop and send an email, chat or push message when it passes a level you choose.
- **Feed other tools.** Forward new rows to Grafana, InfluxDB, a spreadsheet, an MQTT broker or your own API.
- **Combine sources.** Water, weather, satellite and indicator results all arrive in the same format, so one app can show them side by side.
- **Use the meaning, not just the numbers.** The TTL version of each file is linked data that uses the OBEREK
  ontology and metadata, both public on GitHub. The [research tutorial]({{ '/tutorials/research/' | relative_url }}) shows how to query them together.

## Things to know

- **Use the `timestamp` column**, not the file name. The file name is when the pipeline stored the file,
  which can be a second or so later than the reading.
- **Water temperature appears several times per message**, because each of the four sensors at a station
  reports it. Use the `sensor` column to pick one, or average them as the dashboard does.
- **Readings are range-checked, not cleaned.** A water sensor's message is left out when one of its values is outside the
  plausible range in the OBEREK metadata (`nb:SensorRange`, for example 3 to 11 for pH). Values inside the range are passed on
  as measured, so spikes and stuck sensors still show up.
- **Rain is a running total.** Weather station precipitation is the total since local midnight. For the rain in a period, take the difference between two readings.
- **One listing returns at most 1,000 files.** A full day at SouthWest has about 1,440. Use a paginator, or `start-after` as above.
- **Poll no more than once a minute.** New data doesn't arrive any faster.
- **Other formats are next to the CSV.** Swap `csv` for `json` or `ttl` in the key to read single files.
- **The data is provisional.** It is published automatically, before quality checks
  ([data use notice](https://oberek.neverblink.eu/help#data-use-notice)).

- **The pipelines.** [NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code) holds the pipelines that
  collect each source and calculate the indicators, and the ontology and metadata. Code is under Apache 2.0, the ontology and metadata under CC BY 4.0.
- **Licences of the data.** OBEREK, UPV and Fundació Assut data are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Satellite data is under the [Copernicus Sentinel data legal notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice)
  ("Contains modified Copernicus Sentinel data 2026"), and flow data under the
  [CHJ conditions of reuse](https://www.chj.es/es-es/ciudadano/Reutilizacion/Paginas/Condicionesdeuso.aspx).
  The dashboard's [Help page, under Data Sources](https://oberek.neverblink.eu/help), says what to credit for each source.
