---
layout: tutorial
title: Tutorials
lead: Three short guides to using OBEREK, from reading the dashboard to working with the raw sensor data.
description: Tutorials for the OBEREK dashboard, live sensor data and re-deriving the Key Ecological Indicators.
---

<p class="langs-intro"><a href="{{ '/tutorials/dashboard/es/' | relative_url }}" lang="es" hreflang="es">Guía del panel en español</a> · <a href="{{ '/tutorials/dashboard/va/' | relative_url }}" lang="ca-valencia" hreflang="ca-valencia">Guia del tauler en valencià</a></p>

Pick the guide that fits what you want to do. Each one points to the
[Help and documentation page](https://oberek.neverblink.eu/help) on the dashboard for the full definitions.

Everything behind the dashboard is open: the data can be downloaded for free, and the pipelines that collect it and
calculate the indicators, the ontology and the metadata are on GitHub in
[NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code). A snapshot of the data and the code is on
Zenodo ([10.5281/zenodo.23418104](https://doi.org/10.5281/zenodo.23418104)).

<div class="cards">
  <div class="card">
    <span class="who">For everyone · no technical knowledge</span>
    <h3>Read the dashboard</h3>
    <p>What the colours and levels mean, how to pick your area, and what to look at if you farm or fish around l'Albufera.</p>
    <a class="btn" href="{{ '/tutorials/dashboard/' | relative_url }}">Start · 10 min</a>
  </div>
  <div class="card">
    <span class="who">For developers and AI agents</span>
    <h3>Follow a sensor live</h3>
    <p>Connect to the public data bucket, pick up new readings as soon as they arrive, and build your own apps on top. About 20 lines of Python.</p>
    <a class="btn" href="{{ '/tutorials/live-data/' | relative_url }}">Start · 5 min</a>
  </div>
  <div class="card">
    <span class="who">For researchers and data scientists</span>
    <h3>Analyse the data with SPARQL</h3>
    <p>Download the raw data as CSV or RDF, link it to the OBEREK metadata, re-derive what the dashboard shows, and ask your own questions.</p>
    <a class="btn" href="{{ '/tutorials/research/' | relative_url }}">Start · 30 min</a>
  </div>
</div>

<div class="careful" markdown="1">
All OBEREK data is published automatically, before full quality checks. Treat it as provisional
and unofficial ([data use notice](https://oberek.neverblink.eu/help#data-use-notice)).
</div>
