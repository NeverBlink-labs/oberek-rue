---
layout: tutorial
title: Analyse the raw data with metadata and SPARQL
permalink: /tutorials/research/
lead: Download the raw OBEREK sensor data, link it to the OBEREK metadata and ontology, re-derive what the dashboard shows, and ask your own questions with SPARQL.
description: Research tutorial. Work with OBEREK raw data as CSV and linked data (RDF), re-derive dashboard values, and query data and metadata together with SPARQL, using Python, pandas and rdflib.
audience: researchers, data scientists
time: 30 min · Python notebook
---

<p>
  <a class="btn" href="{{ '/tutorials/code/rederive_dashboard.ipynb' | relative_url }}" download>Download the notebook</a>
  <a class="btn secondary" href="https://colab.research.google.com/github/NeverBlink-labs/oberek-rue/blob/main/tutorials/code/rederive_dashboard.ipynb">Open in Google Colab</a>
</p>

## What you'll do

The dashboard shows a summary: one value per day and a status per parameter. Behind it is much more:
every sensor reading, published as CSV and as linked data (RDF), and a metadata graph that describes every
station, sensor, location and reference value. The notebook shows how to use both:

1. **Load the metadata graph** and query it with SPARQL for the reference values and the station's sensors.
2. **Download the raw readings** as CSV, check them against the plausible ranges in the metadata, and see one message as RDF linked to the metadata.
3. **Re-derive the daily series** behind the dashboard charts, and check them against the dashboard.
4. **Re-derive the parameter statuses** (normal, warning, critical) from the reference values.
5. **Ask your own questions with SPARQL** over hours of readings from two stations plus the metadata: what was
   measured where, hourly averages, how many readings crossed their thresholds, and the same results in Valencian.

The notebook reads the [OBEREK metadata](https://github.com/NeverBlink-labs/oberek-code/blob/main/model/oberek-metadata-init/oberek_metadata.ttl)
and [ontology](https://github.com/NeverBlink-labs/oberek-code/blob/main/model/oberek-ontology-init/oberek_ontology.ttl) straight from
[NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code), the open-source repository with the OBEREK pipelines (CC BY 4.0 for
the two files, Apache 2.0 for the code). The reference values in it are the ones on the dashboard's
[Help page](https://oberek.neverblink.eu/help), under "Reference values and thresholds", where their sources are listed too. How the
indicators (KEIs) combine them is explained there in "How the KEIs Are Calculated", and the exact queries are in the repository.

<div class="note" markdown="1">
Below is the notebook with the results of a real run on **{{ site.data.research_capture.captured }}** at the
SouthWest and North stations. Your numbers will be different, because the data keeps coming in.
</div>

{% include research-notebook.md %}

## Next

- Stream the same data as it arrives: [Follow a sensor station in real time]({{ '/tutorials/live-data/' | relative_url }}).
- Explain the dashboard to someone without a technical background: [How to read the OBEREK dashboard]({{ '/tutorials/dashboard/' | relative_url }}).
- Cite the data and code: [doi.org/10.5281/zenodo.23418104](https://doi.org/10.5281/zenodo.23418104) (always points to the newest version).
