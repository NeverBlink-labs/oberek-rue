{% raw %}
This notebook downloads the raw water-quality readings for OBEREK stations, reads the reference
values from the OBEREK metadata graph, and then:

1. recomputes the **daily series** behind every dashboard chart, and checks them against the dashboard,
2. recomputes the **normal / warning / critical status** of each parameter card, and
3. loads the raw data **as linked data** next to the metadata and answers questions with **SPARQL**.

Everything is read-only: the notebook only lists and downloads public files. The metadata and ontology
come from the open-source OBEREK pipelines on GitHub ([NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code)).

The first code cell after the settings installs what the notebook needs (in Google Colab too).

```python
# Settings. The OBEREK metadata and ontology are published with the OBEREK pipelines on GitHub
# (https://github.com/NeverBlink-labs/oberek-code). You can also point these at local copies.
REPO = "https://raw.githubusercontent.com/NeverBlink-labs/oberek-code/main/model"
METADATA = f"{REPO}/oberek-metadata-init/oberek_metadata.ttl"
ONTOLOGY = f"{REPO}/oberek-ontology-init/oberek_ontology.ttl"

STATION = "southwest"   # folder name in the bucket: southwest or north (south sends simulated data)
LOCATION = "SouthWest"  # the same place in the metadata: SouthWest or North
DAYS = 2                # full UTC days to download, plus today so far
HOURS = 6               # hours of linked data to load for the SPARQL questions in section 5
```

```python
%pip install -q boto3 pandas matplotlib rdflib requests  # already installed? this does nothing
```

```python
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import boto3
import matplotlib.pyplot as plt
import pandas as pd
import rdflib
import requests
from botocore import UNSIGNED
from botocore.config import Config

ENDPOINT, BUCKET = "https://oberek.neverblink.eu/s3", "oberek-bucket"
s3 = boto3.client("s3", endpoint_url=ENDPOINT, region_name="us-east-1",
                  config=Config(signature_version=UNSIGNED, max_pool_connections=8,
                                retries={"max_attempts": 5, "mode": "standard"}))
pd.set_option("display.float_format", lambda x: f"{x:,.2f}" if x == 0 or abs(x) >= 0.01 else f"{x:.1e}")
```

## 1. Load the metadata graph

The metadata describes every station, sensor and location. The ontology defines the properties they
measure and the indicators built from them. The reference values that the dashboard uses (a
*baseline*, a *warning* and a *critical* boundary per property) are stored there too, as
`nb:PropertyBaseline` resources, each with the source it comes from. So nothing below needs hard-coded numbers.

```python
g = rdflib.Graph()
g.parse(METADATA, format="turtle")
g.parse(ONTOLOGY, format="turtle")

PREFIXES = """
PREFIX nb:    <https://neverblink.eu/ontologies/oberek/>
PREFIX nbi:   <https://neverblink.eu/oberek/>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX geo:   <http://www.opengis.net/ont/geosparql#>
PREFIX qudt:  <http://qudt.org/schema/qudt/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX s4watr: <https://saref.etsi.org/saref4watr/>
PREFIX bufr4_b13: <http://codes.wmo.int/bufr4/b/13/>
PREFIX owl:   <http://www.w3.org/2002/07/owl#>
PREFIX dcterms: <http://purl.org/dc/terms/>
"""

def short(value):
    """URIs as the same short names used in the CSV files (e.g. bufr4_b13:083); literals as Python values."""
    if isinstance(value, rdflib.URIRef):
        return g.namespace_manager.normalizeUri(value)
    return value.toPython() if value is not None else None

def sparql(query, graph=g):
    result = graph.query(PREFIXES + query)
    return pd.DataFrame([[short(v) for v in row] for row in result], columns=[str(v) for v in result.vars])

print(f"{len(g):,} triples loaded")
```

```text
2,304 triples loaded
```

**Reference values.** One row per property that has a baseline. Warning and critical boundaries are
percentages of deviation from the baseline, counted only in the harmful direction (`nb:Above`,
`nb:Below`, or both when `bidirectional` is true). The last column asks the ontology whether the
property is an input of KEI-1.

```python
baselines = sparql("""
SELECT ?feature ?name ?unit ?baseline ?warning_pct ?critical_pct ?direction ?bidirectional ?kei1_input WHERE {
  ?b a nb:PropertyBaseline ;
     nb:forProperty ?feature ;
     nb:baselineValue ?baseline ;
     nb:warningThreshold ?warning_pct ;
     nb:criticalThreshold ?critical_pct ;
     nb:bidirectional ?bidirectional .
  OPTIONAL { ?b nb:deviationDirection ?direction }
  OPTIONAL { ?feature rdfs:label ?name FILTER(lang(?name) = "en") }
  OPTIONAL { ?feature qudt:applicableUnit ?unit }
  BIND(EXISTS { nb:KEI-1 nb:hasInputFeature ?feature } AS ?kei1_input)
}
ORDER BY DESC(?kei1_input) ?feature
""").set_index("feature")
for col in ["baseline", "warning_pct", "critical_pct"]:
    baselines[col] = baselines[col].astype(float)
baselines
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>name</th>
      <th>unit</th>
      <th>baseline</th>
      <th>warning_pct</th>
      <th>critical_pct</th>
      <th>direction</th>
      <th>bidirectional</th>
      <th>kei1_input</th>
    </tr>
    <tr>
      <th>feature</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>bufr4_b13:083</th>
      <td>Dissolved oxygen</td>
      <td>unit:MilliGM-PER-L</td>
      <td>8.00</td>
      <td>30.00</td>
      <td>60.00</td>
      <td>None</td>
      <td>True</td>
      <td>True</td>
    </tr>
    <tr>
      <th>qudt_qk:Acidity</th>
      <td>pH</td>
      <td>unit:PH</td>
      <td>7.80</td>
      <td>10.00</td>
      <td>15.00</td>
      <td>None</td>
      <td>True</td>
      <td>True</td>
    </tr>
    <tr>
      <th>nb:chlorophyll</th>
      <td>Chlorophyll-a</td>
      <td>unit:MicroGM-PER-L</td>
      <td>5.30</td>
      <td>88.68</td>
      <td>354.72</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>nb:phycocyanin</th>
      <td>Phycocyanin</td>
      <td>unit:MicroGM-PER-L</td>
      <td>30.00</td>
      <td>0.01</td>
      <td>200.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>nb:secchiDiskDepth</th>
      <td>Secchi depth / SDD</td>
      <td>unit:M</td>
      <td>0.60</td>
      <td>33.33</td>
      <td>50.00</td>
      <td>nb:Below</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>s4mari:Salinity</th>
      <td>Salinity</td>
      <td>unit:MilliGM-PER-L</td>
      <td>800.00</td>
      <td>100.00</td>
      <td>300.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>s4mari:WaterConductivity</th>
      <td>Electrical conductivity</td>
      <td>unit:MicroS-PER-CentiM</td>
      <td>1,400.00</td>
      <td>25.00</td>
      <td>50.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>s4mari:WaterTemperature</th>
      <td>Water temperature</td>
      <td>unit:DEG_C</td>
      <td>25.00</td>
      <td>20.00</td>
      <td>32.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>s4watr:Turbidity</th>
      <td>Turbidity</td>
      <td>unit:NTU</td>
      <td>30.00</td>
      <td>50.00</td>
      <td>100.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>wmo:windSpeed</th>
      <td>Wind speed</td>
      <td>unit:M-PER-SEC</td>
      <td>4.00</td>
      <td>40.00</td>
      <td>70.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>False</td>
    </tr>
    <tr>
      <th>nb:pyricularia_risk_index</th>
      <td>Rice Blast Risk Index</td>
      <td>unit:UNITLESS</td>
      <td>0.00</td>
      <td>50.00</td>
      <td>99.00</td>
      <td>nb:Above</td>
      <td>False</td>
      <td>False</td>
    </tr>
  </tbody>
</table>
</div>
</div>

**The station.** Which sensors belong to the station, what each one measures, and its name in the
three dashboard languages. This is what turns a CSV row like `nbi:Estacion_SouthWest-ec` into
"Sensor de conductividad eléctrica".

```python
station = sparql(f"""
SELECT ?sensor ?measures ?name_en ?name_es ?name_va WHERE {{
  nbi:Estacion_{LOCATION} saref:consistsOf ?sensor .
  ?sensor saref:observes ?measures ;
          rdfs:label ?name_en, ?name_es, ?name_va .
  FILTER(lang(?name_en) = "en" && lang(?name_es) = "es" && lang(?name_va) = "ca-valencia")
  FILTER NOT EXISTS {{ ?measures a saref:FeatureOfInterest }}
}}
ORDER BY ?sensor ?measures
""")
station
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sensor</th>
      <th>measures</th>
      <th>name_en</th>
      <th>name_es</th>
      <th>name_va</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nbi:Estacion_SouthWest-ec</td>
      <td>s4mari:Salinity</td>
      <td>Electrical conductivity sensor</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>Sensor de conductivitat elèctrica</td>
    </tr>
    <tr>
      <th>1</th>
      <td>nbi:Estacion_SouthWest-ec</td>
      <td>s4mari:WaterConductivity</td>
      <td>Electrical conductivity sensor</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>Sensor de conductivitat elèctrica</td>
    </tr>
    <tr>
      <th>2</th>
      <td>nbi:Estacion_SouthWest-ec</td>
      <td>s4mari:WaterTemperature</td>
      <td>Electrical conductivity sensor</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>Sensor de conductivitat elèctrica</td>
    </tr>
    <tr>
      <th>3</th>
      <td>nbi:Estacion_SouthWest-ec</td>
      <td>s4watr:TotalDissolvedSolids</td>
      <td>Electrical conductivity sensor</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>Sensor de conductivitat elèctrica</td>
    </tr>
    <tr>
      <th>4</th>
      <td>nbi:Estacion_SouthWest-oxygen</td>
      <td>bufr4_b13:083</td>
      <td>Dissolved oxygen sensor</td>
      <td>Sensor de oxígeno disuelto</td>
      <td>Sensor d'oxigen dissolt</td>
    </tr>
    <tr>
      <th>5</th>
      <td>nbi:Estacion_SouthWest-oxygen</td>
      <td>s4mari:WaterTemperature</td>
      <td>Dissolved oxygen sensor</td>
      <td>Sensor de oxígeno disuelto</td>
      <td>Sensor d'oxigen dissolt</td>
    </tr>
    <tr>
      <th>6</th>
      <td>nbi:Estacion_SouthWest-ph</td>
      <td>qudt_qk:Acidity</td>
      <td>pH sensor</td>
      <td>Sensor de pH</td>
      <td>Sensor de pH</td>
    </tr>
    <tr>
      <th>7</th>
      <td>nbi:Estacion_SouthWest-ph</td>
      <td>s4mari:WaterTemperature</td>
      <td>pH sensor</td>
      <td>Sensor de pH</td>
      <td>Sensor de pH</td>
    </tr>
    <tr>
      <th>8</th>
      <td>nbi:Estacion_SouthWest-turbidity</td>
      <td>s4mari:WaterTemperature</td>
      <td>Turbidity sensor</td>
      <td>Sensor de turbidez</td>
      <td>Sensor de terbolesa</td>
    </tr>
    <tr>
      <th>9</th>
      <td>nbi:Estacion_SouthWest-turbidity</td>
      <td>s4watr:Turbidity</td>
      <td>Turbidity sensor</td>
      <td>Sensor de turbidez</td>
      <td>Sensor de terbolesa</td>
    </tr>
  </tbody>
</table>
</div>
</div>

**Plausible ranges.** Each water measurement also has a plausible range (`nb:SensorRange`). OBEREK leaves out any
sensor message with a value outside it, so every reading you download is inside these limits. They are also a handy
first filter if you combine OBEREK data with readings from other sensors.

```python
sparql("""
SELECT ?feature ?name ?min ?max WHERE {
  ?r a nb:SensorRange ; nb:forProperty ?feature ; nb:plausibleMin ?min ; nb:plausibleMax ?max .
  OPTIONAL { ?feature rdfs:label ?name FILTER(lang(?name) = "en") }
}
ORDER BY ?feature
""")
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>feature</th>
      <th>name</th>
      <th>min</th>
      <th>max</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>bufr4_b13:083</td>
      <td>Dissolved oxygen</td>
      <td>0</td>
      <td>25</td>
    </tr>
    <tr>
      <th>1</th>
      <td>qudt_qk:Acidity</td>
      <td>pH</td>
      <td>3</td>
      <td>11</td>
    </tr>
    <tr>
      <th>2</th>
      <td>s4mari:Salinity</td>
      <td>Salinity</td>
      <td>0</td>
      <td>10000</td>
    </tr>
    <tr>
      <th>3</th>
      <td>s4mari:WaterConductivity</td>
      <td>Electrical conductivity</td>
      <td>0</td>
      <td>10000</td>
    </tr>
    <tr>
      <th>4</th>
      <td>s4mari:WaterTemperature</td>
      <td>Water temperature</td>
      <td>-5</td>
      <td>50</td>
    </tr>
    <tr>
      <th>5</th>
      <td>s4watr:TotalDissolvedSolids</td>
      <td>Total dissolved solids</td>
      <td>0</td>
      <td>10000</td>
    </tr>
    <tr>
      <th>6</th>
      <td>s4watr:Turbidity</td>
      <td>Turbidity</td>
      <td>0</td>
      <td>2000</td>
    </tr>
  </tbody>
</table>
</div>
</div>

## 2. Get the raw data

Every message from the station is stored as one file per format under
`raw/iot/<station>/<format>/<YYYY-MM-DD>/`. The CSV version is easiest for pandas.
At SouthWest that's about 1,440 small files a day, so this cell downloads a few thousand files and can
take a minute. The [live-data tutorial](https://neverblink-labs.github.io/oberek-rue/tutorials/live-data/)
explains the folder layout.

```python
def list_keys(prefix):
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        keys += [obj["Key"] for obj in page.get("Contents", [])]
    return keys

def read_csv(key):
    return pd.read_csv(io.BytesIO(s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()))

def read_many(keys):
    with ThreadPoolExecutor(8) as pool:
        frames = list(pool.map(read_csv, keys))
    data = pd.concat(frames, ignore_index=True)
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    return data

today = datetime.now(timezone.utc).date()
days = [today - timedelta(days=n) for n in range(DAYS, -1, -1)]
keys = [k for day in days for k in list_keys(f"raw/iot/{STATION}/csv/{day}/")]
iot = read_many(keys).dropna(subset=["value"])
print(f"{len(keys):,} files, {len(iot):,} readings from {iot.timestamp.min():%Y-%m-%d %H:%M} "
      f"to {iot.timestamp.max():%Y-%m-%d %H:%M} UTC")
iot.head()
```

```text
3,004 files, 30,040 readings from 2026-10-14 00:00 to 2026-10-16 17:53 UTC
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>timestamp</th>
      <th>device</th>
      <th>sensor</th>
      <th>feature</th>
      <th>statistic_type</th>
      <th>unit</th>
      <th>value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2026-10-14 00:00:06.284000+00:00</td>
      <td>nbi:Estacion_SouthWest</td>
      <td>nbi:Estacion_SouthWest-ec</td>
      <td>s4mari:Salinity</td>
      <td>NaN</td>
      <td>unit:MilliGM-PER-L</td>
      <td>855.00</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2026-10-14 00:00:06.284000+00:00</td>
      <td>nbi:Estacion_SouthWest</td>
      <td>nbi:Estacion_SouthWest-turbidity</td>
      <td>s4mari:WaterTemperature</td>
      <td>NaN</td>
      <td>unit:DEG_C</td>
      <td>18.70</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2026-10-14 00:00:06.284000+00:00</td>
      <td>nbi:Estacion_SouthWest</td>
      <td>nbi:Estacion_SouthWest-ec</td>
      <td>s4mari:WaterTemperature</td>
      <td>NaN</td>
      <td>unit:DEG_C</td>
      <td>23.90</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2026-10-14 00:00:06.284000+00:00</td>
      <td>nbi:Estacion_SouthWest</td>
      <td>nbi:Estacion_SouthWest-ph</td>
      <td>s4mari:WaterTemperature</td>
      <td>NaN</td>
      <td>unit:DEG_C</td>
      <td>23.96</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2026-10-14 00:00:06.284000+00:00</td>
      <td>nbi:Estacion_SouthWest</td>
      <td>nbi:Estacion_SouthWest-turbidity</td>
      <td>s4watr:Turbidity</td>
      <td>NaN</td>
      <td>unit:NTU</td>
      <td>371.30</td>
    </tr>
  </tbody>
</table>
</div>
</div>

**The same data as RDF.** Each CSV file has a Turtle (`.ttl`) twin. It uses the same vocabulary as the
metadata, so you can load one next to the metadata graph and query both together. Here we read the newest
message and join each value with the sensor's Spanish name and the location it belongs to. Neither
of those is in the observation file; both come from the metadata.

```python
ttl_key = list_keys(f"raw/iot/{STATION}/ttl/{today}/")[-1]  # the newest message
ttl_text = s3.get_object(Bucket=BUCKET, Key=ttl_key)["Body"].read().decode()
combined = g + rdflib.Graph().parse(data=ttl_text, format="turtle")

sparql("""
SELECT ?time ?sensor_es ?property ?value ?unit ?location WHERE {
  ?sensor saref:madeExecution ?obs .
  ?obs saref:hasTimestamp ?time ;
       saref:hasResult [ saref:isValueOfProperty ?property ; saref:hasValue ?value ; saref:isMeasuredIn ?unit ] .
  ?sensor rdfs:label ?sensor_es FILTER(lang(?sensor_es) = "es")
  ?sensor saref:observes ?location . ?location a saref:FeatureOfInterest .
}
ORDER BY ?sensor_es ?property
""", graph=combined)
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>time</th>
      <th>sensor_es</th>
      <th>property</th>
      <th>value</th>
      <th>unit</th>
      <th>location</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>s4mari:Salinity</td>
      <td>861.00</td>
      <td>unit:MilliGM-PER-L</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>s4mari:WaterConductivity</td>
      <td>1,565.00</td>
      <td>unit:MicroS-PER-CentiM</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>s4mari:WaterTemperature</td>
      <td>26.30</td>
      <td>unit:DEG_C</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de conductividad eléctrica</td>
      <td>s4watr:TotalDissolvedSolids</td>
      <td>783.00</td>
      <td>unit:MilliGM-PER-L</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de oxígeno disuelto</td>
      <td>bufr4_b13:083</td>
      <td>11.32</td>
      <td>unit:MilliGM-PER-L</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>5</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de oxígeno disuelto</td>
      <td>s4mari:WaterTemperature</td>
      <td>24.30</td>
      <td>unit:DEG_C</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>6</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de pH</td>
      <td>qudt_qk:Acidity</td>
      <td>7.56</td>
      <td>unit:PH</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>7</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de pH</td>
      <td>s4mari:WaterTemperature</td>
      <td>26.54</td>
      <td>unit:DEG_C</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>8</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de turbidez</td>
      <td>s4mari:WaterTemperature</td>
      <td>19.10</td>
      <td>unit:DEG_C</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
    <tr>
      <th>9</th>
      <td>2026-10-16 17:54:06.837000+00:00</td>
      <td>Sensor de turbidez</td>
      <td>s4watr:Turbidity</td>
      <td>998.70</td>
      <td>unit:NTU</td>
      <td>nbi:Location-SouthWest</td>
    </tr>
  </tbody>
</table>
</div>
</div>

## 3. Rebuild the dashboard's daily series

Each chart on the dashboard reads a small JSON file with one value per UTC day for the last 30 days:
`<location>/raw/iot/<feature>/latest.json`. OBEREK makes it by averaging every reading of the day. For
water temperature, that includes all four sensors at the station. Let's do the same and compare.

```python
KEY_SEGMENT = {"SouthWest": "sw", "North": "north", "South": "south"}[LOCATION]

def dashboard_series(feature):
    prefix, name = feature.split(":")
    if name[0].isdigit():         # numeric WMO codes keep their prefix: bufr4_b13-083
        name = f"{prefix}-{name}"
    url = f"{ENDPOINT}/{BUCKET}/{KEY_SEGMENT}/raw/iot/{name}/latest.json"
    points = requests.get(url, timeout=30).json()["data"]
    return pd.Series({pd.Timestamp(p["timestamp"]).date(): p["value"] for p in points}, name="dashboard")

daily = iot.groupby([iot.timestamp.dt.date, "feature"]).value.mean().unstack()
full_days = [d for d in daily.index if d < today]  # today is not finished yet

rows = []
for feature in daily.columns:
    theirs = dashboard_series(feature)
    for day in full_days:
        if day in theirs.index:
            rows.append({"day": day, "feature": feature, "re-derived": daily.loc[day, feature],
                         "dashboard": theirs[day]})
compare = pd.DataFrame(rows)
compare["difference %"] = 100 * (compare["re-derived"] - compare["dashboard"]).abs() / compare["dashboard"].abs()
compare.groupby("feature")["difference %"].max().to_frame("largest difference, % of value")
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>largest difference, % of value</th>
    </tr>
    <tr>
      <th>feature</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>bufr4_b13:083</th>
      <td>4.7e-05</td>
    </tr>
    <tr>
      <th>qudt_qk:Acidity</th>
      <td>2.9e-04</td>
    </tr>
    <tr>
      <th>s4mari:Salinity</th>
      <td>2.9e-06</td>
    </tr>
    <tr>
      <th>s4mari:WaterConductivity</th>
      <td>1.4e-06</td>
    </tr>
    <tr>
      <th>s4mari:WaterTemperature</th>
      <td>1.4e-04</td>
    </tr>
    <tr>
      <th>s4watr:TotalDissolvedSolids</th>
      <td>2.7e-06</td>
    </tr>
    <tr>
      <th>s4watr:Turbidity</th>
      <td>6.6e-04</td>
    </tr>
  </tbody>
</table>
</div>
</div>

The differences are rounding noise: OBEREK averages and stores the values as 32-bit floats. Today is left out on purpose: the
dashboard calculates today's point during the day, so it is based on fewer readings than ours. The chart below
shows how much one daily point hides. The minute readings are grey and the daily means are green. The
orange crosses are the dashboard's published points.

```python
feature = "s4watr:Turbidity"
theirs = dashboard_series(feature)
minute = iot[(iot.feature == feature) & (iot.timestamp.dt.date < today)]  # full days only
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(minute.timestamp, minute.value, color="#9aa59a", lw=0.8, label="every reading")
mid = lambda d: pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=12)
ax.plot([mid(d) for d in full_days], daily.loc[full_days, feature], "o-", color="#2a7c5e", label="re-derived daily mean")
shown = theirs[[d for d in full_days if d in theirs.index]]
ax.plot([mid(d) for d in shown.index], shown.values, "x", color="#f4a261", ms=10, mew=2, label="dashboard")
ax.set_title(f"{baselines.loc[feature, 'name']} at {LOCATION} (NTU)", loc="left")
ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.3)
plt.show()
```

<img src="../../assets/tutorials/img/research/figure-1.png" alt="Turbidity at the station: every reading as a grey line, with re-derived daily means and the dashboard's daily points on top" loading="lazy">

## 4. Rebuild the parameter-card colours

Each parameter card on the dashboard is green, orange or red. The rule has three steps:

1. relative deviation from the baseline: `d = (x − baseline) / baseline`,
2. keep only the harmful side: `max(d, 0)` for *Above*, `max(−d, 0)` for *Below*, `|d|` for bidirectional,
3. **warning** if that is ≥ the warning %, **critical** if it is > the critical %.

This is the same rule the KEI pipelines use (see `pipeline/kei-1-processing/manifest.yml` in
[oberek-code](https://github.com/NeverBlink-labs/oberek-code)). The pipelines apply it to the last hour of readings,
every 15 minutes. Here we apply it to the last full day, like the dashboard cards.

```python
def directed_deviation(value, feature, refs=baselines):
    r = refs.loc[feature]
    d = (value - r.baseline) / (r.baseline + 1e-6)
    if r.bidirectional:
        return abs(d)
    return max(d, 0.0) if r.direction == "nb:Above" else max(-d, 0.0)

def card_status(value, feature, refs=baselines):
    dd, r = directed_deviation(value, feature, refs), refs.loc[feature]
    return "critical" if dd > r.critical_pct / 100 else "warning" if dd >= r.warning_pct / 100 else "normal"

latest_day = full_days[-1]
cards = pd.DataFrame([
    {"parameter": baselines.loc[f, "name"], "latest daily value": daily.loc[latest_day, f],
     "deviation %": 100 * directed_deviation(daily.loc[latest_day, f], f), "status": card_status(daily.loc[latest_day, f], f)}
    for f in daily.columns if f in baselines.index
])
print(f"Status on {latest_day}")
cards
```

```text
Status on 2026-10-15
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>parameter</th>
      <th>latest daily value</th>
      <th>deviation %</th>
      <th>status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Dissolved oxygen</td>
      <td>9.77</td>
      <td>22.14</td>
      <td>normal</td>
    </tr>
    <tr>
      <th>1</th>
      <td>pH</td>
      <td>7.36</td>
      <td>5.65</td>
      <td>normal</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Salinity</td>
      <td>836.40</td>
      <td>4.55</td>
      <td>normal</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Electrical conductivity</td>
      <td>1,520.68</td>
      <td>8.62</td>
      <td>normal</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Water temperature</td>
      <td>22.23</td>
      <td>0.00</td>
      <td>normal</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Turbidity</td>
      <td>998.70</td>
      <td>3,229.00</td>
      <td>critical</td>
    </tr>
  </tbody>
</table>
</div>
</div>

## 5. Ask your own questions with SPARQL

So far we used pandas on the CSV files. The same readings are also published as linked data (TTL), using the
vocabulary of the OBEREK metadata and ontology. Load them into the same graph as the metadata, and every reading is
automatically connected to its sensor, its location, the property it measures, the property's names in three
languages, its reference values, and the indicators it feeds. One SPARQL query can then use all of that at once.

Here we load the last few hours from **both** real stations, SouthWest and North.

```python
def list_after(prefix, after=""):
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix, StartAfter=after):
        keys += [obj["Key"] for obj in page.get("Contents", [])]
    return keys

def read_text(key):
    return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()

since = datetime.now(timezone.utc) - timedelta(hours=HOURS)
ttl_keys = []
for station in ["southwest", "north"]:
    for day in sorted({since.date(), today}):
        prefix = f"raw/iot/{station}/ttl/{day}/"
        ttl_keys += list_after(prefix, prefix + f"data_{since:%H_%M_%S}.ttl" if day == since.date() else "")

with ThreadPoolExecutor(8) as pool:
    documents = list(pool.map(read_text, ttl_keys))
kg = g + rdflib.Graph()          # a copy of the metadata graph…
for doc in documents:            # …plus every observation file
    kg.parse(data=doc, format="turtle")
print(f"{len(ttl_keys)} files, {len(kg):,} triples in the combined graph")
```

```text
314 files, 30,564 triples in the combined graph
```

**What was measured, where, and when?** The observation files only say which sensor made a reading. The location
and the plain name of what it measures come from the metadata.

```python
sparql("""
SELECT ?place ?measurement (COUNT(?value) AS ?readings) (MIN(?time) AS ?first) (MAX(?time) AS ?last) WHERE {
  ?sensor saref:madeExecution ?obs ;
          saref:observes ?location .
  ?location a saref:FeatureOfInterest ; rdfs:label ?place . FILTER(lang(?place) = "en")
  ?obs saref:hasTimestamp ?time ;
       saref:hasResult [ saref:isValueOfProperty ?property ; saref:hasValue ?value ] .
  ?property rdfs:label ?measurement . FILTER(lang(?measurement) = "en")
}
GROUP BY ?place ?measurement
ORDER BY ?place ?measurement
""", graph=kg)
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>place</th>
      <th>measurement</th>
      <th>readings</th>
      <th>first</th>
      <th>last</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>North</td>
      <td>Dissolved oxygen</td>
      <td>37</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>1</th>
      <td>North</td>
      <td>Electrical conductivity</td>
      <td>37</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>2</th>
      <td>North</td>
      <td>Salinity</td>
      <td>37</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>3</th>
      <td>North</td>
      <td>Total dissolved solids</td>
      <td>37</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>4</th>
      <td>North</td>
      <td>Turbidity</td>
      <td>37</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>5</th>
      <td>North</td>
      <td>Water temperature</td>
      <td>148</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>6</th>
      <td>North</td>
      <td>pH</td>
      <td>37</td>
      <td>2026-10-16 12:00:14+00:00</td>
      <td>2026-10-16 17:50:32+00:00</td>
    </tr>
    <tr>
      <th>7</th>
      <td>South-West</td>
      <td>Dissolved oxygen</td>
      <td>277</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
    <tr>
      <th>8</th>
      <td>South-West</td>
      <td>Electrical conductivity</td>
      <td>277</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
    <tr>
      <th>9</th>
      <td>South-West</td>
      <td>Salinity</td>
      <td>277</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
    <tr>
      <th>10</th>
      <td>South-West</td>
      <td>Total dissolved solids</td>
      <td>277</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
    <tr>
      <th>11</th>
      <td>South-West</td>
      <td>Turbidity</td>
      <td>277</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
    <tr>
      <th>12</th>
      <td>South-West</td>
      <td>Water temperature</td>
      <td>1108</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
    <tr>
      <th>13</th>
      <td>South-West</td>
      <td>pH</td>
      <td>277</td>
      <td>2026-10-16 11:56:06.786000+00:00</td>
      <td>2026-10-16 17:54:06.837000+00:00</td>
    </tr>
  </tbody>
</table>
</div>
</div>

**How does dissolved oxygen change hour by hour at each station?** SPARQL does the grouping. We only draw the
result.

```python
hourly = sparql("""
SELECT ?place ?hour (AVG(?value) AS ?oxygen) WHERE {
  ?sensor saref:madeExecution ?obs ;
          saref:observes ?location .
  ?location a saref:FeatureOfInterest ; rdfs:label ?place . FILTER(lang(?place) = "en")
  ?obs saref:hasTimestamp ?time ;
       saref:hasResult [ saref:isValueOfProperty bufr4_b13:083 ; saref:hasValue ?value ] .
  BIND(SUBSTR(STR(?time), 1, 13) AS ?hour)
}
GROUP BY ?place ?hour
ORDER BY ?hour
""", graph=kg)
hourly["hour"] = pd.to_datetime(hourly["hour"] + ":00Z")

fig, ax = plt.subplots(figsize=(9, 3))
for (place, rows), color in zip(hourly.groupby("place"), ["#2a7c5e", "#f4a261"]):
    ax.plot(rows.hour, rows.oxygen.astype(float), "o-", color=color, label=place)
ax.set_title("Dissolved oxygen, hourly average (mg/L)", loc="left")
ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.3)
plt.show()
```

<img src="../../assets/tutorials/img/research/figure-2.png" alt="Hourly average dissolved oxygen at the SouthWest and North stations, computed with SPARQL" loading="lazy">

**How many readings crossed their thresholds?** This query joins every reading with its reference value and
thresholds from the metadata, and follows the ontology to keep only the properties that feed KEI-1
(`nb:KEI-1 nb:hasInputFeature`). The deviation rule is the same one used in section 4.

```python
sparql("""
SELECT ?place ?measurement (COUNT(?value) AS ?readings)
       (SUM(IF(?deviation >= ?warning / 100, 1, 0)) AS ?over_warning)
       (SUM(IF(?deviation > ?critical / 100, 1, 0)) AS ?over_critical) WHERE {
  ?sensor saref:madeExecution ?obs .
  ?obs saref:hasResult ?result .
  ?result saref:isValueOfProperty ?property ; saref:hasValue ?value .
  nb:KEI-1 nb:hasInputFeature ?property .
  ?b nb:forProperty ?property ;
     nb:baselineValue ?baseline ;
     nb:warningThreshold ?warning ;
     nb:criticalThreshold ?critical ;
     nb:bidirectional ?both .
  OPTIONAL { ?b nb:deviationDirection ?direction }
  ?sensor saref:observes ?location .
  ?location a saref:FeatureOfInterest ; rdfs:label ?place . FILTER(lang(?place) = "en")
  ?property rdfs:label ?measurement . FILTER(lang(?measurement) = "en")
  BIND((?value - ?baseline) / ?baseline AS ?d)
  BIND(IF(?both, ABS(?d), IF(?direction = nb:Above, IF(?d > 0, ?d, 0), IF(?d < 0, -?d, 0))) AS ?deviation)
}
GROUP BY ?place ?measurement
ORDER BY ?place ?measurement
""", graph=kg)
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>place</th>
      <th>measurement</th>
      <th>readings</th>
      <th>over_warning</th>
      <th>over_critical</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>North</td>
      <td>Dissolved oxygen</td>
      <td>37</td>
      <td>4</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>North</td>
      <td>Electrical conductivity</td>
      <td>37</td>
      <td>37</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>North</td>
      <td>Salinity</td>
      <td>37</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>North</td>
      <td>Turbidity</td>
      <td>37</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>North</td>
      <td>Water temperature</td>
      <td>148</td>
      <td>11</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <td>North</td>
      <td>pH</td>
      <td>37</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <td>South-West</td>
      <td>Dissolved oxygen</td>
      <td>277</td>
      <td>124</td>
      <td>29</td>
    </tr>
    <tr>
      <th>7</th>
      <td>South-West</td>
      <td>Electrical conductivity</td>
      <td>277</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <td>South-West</td>
      <td>Salinity</td>
      <td>277</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <td>South-West</td>
      <td>Turbidity</td>
      <td>277</td>
      <td>277</td>
      <td>277</td>
    </tr>
    <tr>
      <th>10</th>
      <td>South-West</td>
      <td>Water temperature</td>
      <td>1108</td>
      <td>83</td>
      <td>0</td>
    </tr>
    <tr>
      <th>11</th>
      <td>South-West</td>
      <td>pH</td>
      <td>277</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>
</div>

**The same answer in Valencian.** Ask for the labels in another language and the whole result changes language.
The metadata has English (`en`), Spanish (`es`) and Valencian (`ca-valencia`).

```python
sparql("""
SELECT ?lloc ?mesura (ROUND(AVG(?value) * 100) / 100 AS ?mitjana) WHERE {
  ?sensor saref:madeExecution ?obs ;
          saref:observes ?location .
  ?location a saref:FeatureOfInterest ; rdfs:label ?lloc . FILTER(lang(?lloc) = "ca-valencia")
  ?obs saref:hasResult [ saref:isValueOfProperty ?property ; saref:hasValue ?value ] .
  ?property rdfs:label ?mesura . FILTER(lang(?mesura) = "ca-valencia")
}
GROUP BY ?lloc ?mesura
ORDER BY ?mesura ?lloc
""", graph=kg)
```

<div class="table-scroll output">
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>lloc</th>
      <th>mesura</th>
      <th>mitjana</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Nord</td>
      <td>Conductivitat elèctrica</td>
      <td>2079.19</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Sud-oest</td>
      <td>Conductivitat elèctrica</td>
      <td>1585.51</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Nord</td>
      <td>Oxigen dissolt</td>
      <td>7.23</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Sud-oest</td>
      <td>Oxigen dissolt</td>
      <td>10.22</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Nord</td>
      <td>Salinitat</td>
      <td>1143.22</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Sud-oest</td>
      <td>Salinitat</td>
      <td>872.08</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Nord</td>
      <td>Sòlids dissolts totals</td>
      <td>1039.59</td>
    </tr>
    <tr>
      <th>7</th>
      <td>Sud-oest</td>
      <td>Sòlids dissolts totals</td>
      <td>792.99</td>
    </tr>
    <tr>
      <th>8</th>
      <td>Nord</td>
      <td>Temperatura de l’aigua</td>
      <td>25.28</td>
    </tr>
    <tr>
      <th>9</th>
      <td>Sud-oest</td>
      <td>Temperatura de l’aigua</td>
      <td>24.3</td>
    </tr>
    <tr>
      <th>10</th>
      <td>Nord</td>
      <td>Terbolesa</td>
      <td>38.26</td>
    </tr>
    <tr>
      <th>11</th>
      <td>Sud-oest</td>
      <td>Terbolesa</td>
      <td>998.7</td>
    </tr>
    <tr>
      <th>12</th>
      <td>Nord</td>
      <td>pH</td>
      <td>7.89</td>
    </tr>
    <tr>
      <th>13</th>
      <td>Sud-oest</td>
      <td>pH</td>
      <td>7.43</td>
    </tr>
  </tbody>
</table>
</div>
</div>

**Save your work.** Write the re-derived daily series and the hourly averages to CSV:

```python
daily.to_csv(f"oberek_{STATION}_daily.csv")
hourly.to_csv("oberek_oxygen_hourly.csv", index=False)
print("saved", f"oberek_{STATION}_daily.csv", "oberek_oxygen_hourly.csv")
```

```text
saved oberek_southwest_daily.csv oberek_oxygen_hourly.csv
```

## Good to know

* **The data is provisional.** It is published automatically, before quality checks, and the
  baselines are under scientific review
  ([data use notice](https://oberek.neverblink.eu/help#data-use-notice)).
* **The indicators (KEI-1, KEI-2, KEI-3)** combine these statuses into levels from 1 to 5. The dashboard's
  [Help page](https://oberek.neverblink.eu/help), section "How the KEIs Are Calculated", explains the method.
  OBEREK publishes its own results every 15 minutes under `keis/kei-1/csv/`, `keis/kei-2/csv/` and `keis/kei-3/csv/`.
  The South water station currently sends simulated data, so the results for the South and Global locations are not real yet.
* **The pipelines are open source.** The exact queries behind the indicators are in
  [NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code): the KEIs in `pipeline/kei-*-processing/`,
  the rice blast index in `pipeline/pri/`, and the ingestion of each source in `pipeline/*-ingestion/`. Start there if you
  want to change a rule, try other reference values, or set up the same indicators for another site.
* **Need a longer period?** A snapshot of everything collected up to 15 October 2026 is on Zenodo,
  in the same folder layout and formats: [doi.org/10.5281/zenodo.23418104](https://doi.org/10.5281/zenodo.23418104).
  Its README lists the period covered for each source.
* **Weather, satellite and flow data** are in the same bucket and are loaded the same way. The
  [live-data tutorial](https://neverblink-labs.github.io/oberek-rue/tutorials/live-data/) lists the folders.
{% endraw %}
