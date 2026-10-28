---
layout: tutorial
lang: en
ref: dashboard
title: How to read the OBEREK dashboard
permalink: /tutorials/dashboard/
lead: A step-by-step guide to the dashboard for l'Albufera. No technical knowledge needed.
description: Plain-language guide to the OBEREK dashboard for farmers, fishers and residents of l'Albufera de València.
audience: farmers, fishers, residents, everyone
time: 10 minutes
printable: true
---

The OBEREK dashboard is a **health check for l'Albufera**. Water sensors, a weather station, flow gauging stations,
satellites and people like you send in information, and the dashboard turns it into a few simple signs:

- **Water**: how clean the water in the lagoon and the channels is.
- **Habitat**: how well the water and the land around it support plants, fish and birds. This includes the risk of rice blast.
- **What people think**: how local people rate the area, compared with what the measurements say.

You don't need an account. It works on a phone, tablet or computer.

<section class="part" markdown="1">
<span class="part-label">Part 1</span>

## Open the dashboard

<ol class="steps">
<li><strong>Go to <a href="https://oberek.neverblink.eu">oberek.neverblink.eu</a>.</strong>
Use any web browser. You can save it to your phone's home screen to find it again easily.
{% include shot.html id="overview" caption="The main page on a computer. (1) The menu with every page. (2) The locations you can choose. (3) The three indicator cards. (4) The community poll, shown when Global is selected. (5) Language." %}
</li>
<li><strong>Choose your language.</strong>
The dashboard speaks English, Spanish and Valencian. Change the language in the menu at the bottom left on a computer (5 above), or at the top right on a phone (1 below).
{% include shot.html id="phone" caption="On a phone. (1) Language. (2) The locations you can choose. (3) The menu moves to the bottom of the screen." %}
</li>
</ol>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 2</span>

## Choose your location

<ol class="steps">
<li><strong>Tap one of the location buttons at the top.</strong>
<b>Global</b> is the whole lagoon. <b>Location N</b> (north, Sèquia de Ravisanxo), <b>Location S</b> (south, Sèquia Obera) and <b>Location SW</b> (south-west, Sèquia de Rizarbe) are the three locations with water sensors. Every page then shows the location you chose.
{% include shot.html id="locations-map" caption="The Help page map. Blue pins are the three locations with water sensors; orange circles are the six flow gauging stations of the Júcar river authority (CHJ)." %}
</li>
<li><strong>Pick the location closest to your fields or fishing area.</strong>
The dashboard remembers your choice for the next visit.</li>
</ol>

<div class="tip" markdown="1">
Some information only exists for some locations. Weather and rice blast risk come from one weather station,
**Tancat de l'Estell**, which belongs to **Location S**. Opinion poll results and water flow are for the whole lagoon,
so choose **Global** to see them. If a tab or section is missing, that information is not collected for the location you chose.
</div>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 3</span>

## Read the three cards on the main page

<ol class="steps">
<li><strong>Find the name of the card (1).</strong>
KEI means "key ecological indicator": one of the three health signs. KEI-1 is water, KEI-2 is habitat, KEI-3 is what people think.
{% include shot.html id="kei-cards" caption="(1) The indicator. (2) Its level today, in words and as a number out of 5. (3) How it changed over the last 30 days." %}
</li>
<li><strong>Look at the coloured label (2). 5 is the best, 1 is the worst.</strong>
For water (KEI-1), the Help page describes the levels like this (in short):
<div class="levels">
  <div class="level l5"><b>5 · Very good</b>No measurement has crossed its warning threshold.</div>
  <div class="level l4"><b>4 · Good</b>Minor deviations, but overall conditions remain favourable.</div>
  <div class="level l3"><b>3 · Moderate concern</b>Several measurements differ from the target and should be watched closely.</div>
  <div class="level l2"><b>2 · Poor</b>The measurements are clearly worse than they should be.</div>
  <div class="level l1"><b>1 · Critical</b>Severely worse than they should be, and/or several measurements have crossed their critical threshold.</div>
</div>
The level depends on how many measurements are out of range and how far. Help &amp; Documentation, section
<b>"How the KEIs Are Calculated"</b>, explains the exact steps and describes the levels for each indicator.
</li>
<li><strong>Look at the line (3) to see which way things are going.</strong>
The line shows the score for each of the last 30 days, from 0 to 100, with higher meaning better. A line going down means conditions are getting worse, even if the label still says "Good".</li>
</ol>

<div class="careful" markdown="1">
**KEI-3 works differently.** A high KEI-3 does not mean the lagoon is healthy. It means people's opinions and the
measurements **agree**. A low KEI-3 means people see things differently from what the sensors show.
</div>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 4</span>

## Look closer at the water (KEI-1)

<ol class="steps">
<li><strong>Open "KEI-1 Water Quality" from the menu.</strong>
At the top you see the water score over the last 30 days, with today's level in the corner (1).
{% include shot.html id="kei1-trend" caption="(1) Today's level. (2) The score for each day. 100 is the best possible." %}
</li>
<li><strong>Scroll down to the measurement cards.</strong>
Each card is one thing the water sensors measure. The line under the name says where the data comes from: here the
OBEREK sensor station, run with the Universitat Politècnica de València (UPV). The label in the corner (2) compares the latest daily value (3) with two limits
that OBEREK sets for each measurement: a <b>warning threshold</b> and a <b>critical threshold</b>. Both are set as a distance from a
<b>reference value</b>, the value expected for l'Albufera. Only changes in the harmful direction count: for example, turbidity only when it is too high, but pH when it is too high or too low.
<ul>
<li><span class="chip normal">● NORMAL</span>: the value has not reached the warning threshold.</li>
<li><span class="chip warning">● WARNING</span>: the value has crossed the warning threshold.</li>
<li><span class="chip critical">● CRITICAL</span>: the value has crossed the critical threshold.</li>
</ul>
{% include shot.html id="kei1-cards" caption="(1) What is measured. (2) Its status. (3) The latest daily value. (4) A measurement that needs attention, when there is one." %}
</li>
<li><strong>Know what each measurement means.</strong>
Short summaries of the Help page's "Parameter Descriptions":
<div class="table-scroll" markdown="1">

| On the card | What it measures | Counts against the threshold when it is |
|---|---|---|
| pH | How acidic or alkaline the water is. | too high or too low |
| Dissolved oxygen | The oxygen available in the water for fish and other aquatic life. 0 mg/L means no oxygen at all. | too high or too low |
| Salinity | The amount of dissolved salts in the water. | too high |
| Electrical conductivity | How well the water conducts electricity. This is closely related to the amount of dissolved salts. | too high |
| Turbidity | How cloudy the water is. More particles means less light for underwater plants. | too high |
| Water temperature | The temperature of the water. Warmer water holds less oxygen and helps algae grow. | too high |

</div>
</li>
<li><strong>Switch to "Satellite" to see the lagoon from space.</strong>
The Copernicus Sentinel-2 satellite estimates <b>chlorophyll-a</b> (a pigment in algae, used as a measure of how much algae there is), <b>phycocyanin</b> (a pigment of cyanobacteria, also called blue-green algae) and <b>Secchi depth</b> (how clear the water is; higher means clearer). Chlorophyll-a and phycocyanin count against their thresholds when they are too high, and Secchi depth when it is too low. The buttons above the map (2) change what the map (3) shows. The colour bar under the map marks where the warning and critical thresholds are.
{% include shot.html id="kei1-satellite" caption="(1) Status of the satellite measurement. (2) Choose what the map shows. (3) The map of the area." %}
</li>
</ol>

<div class="tip" markdown="1">
**The satellite looks at open water near your location, not at the location itself.** The sensor sites are in channels
between rice fields, where a satellite can't measure water quality, so each location is paired with the closest stretch of open
lagoon. A new value only appears when the satellite passes over on a day with little cloud, so the line can stay flat for several days.
</div>

<div class="careful" markdown="1">
**A single very tall spike in a chart is often a sensor problem, not a real change in the water.**
Sensors sometimes send a wrong value for a few minutes. Look at the days around it before drawing conclusions.
</div>

<div class="tip" markdown="1">
**Where are the exact numbers?** Open [Help & Documentation](https://oberek.neverblink.eu/help) and scroll to
**"Reference values and thresholds"**. It lists the reference value, the warning threshold and the critical threshold
for every measurement, and where each value comes from (a regulation, a scientific paper or the project's own judgement).
These values are provisional and still under scientific review.
</div>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 5</span>

## Check the habitat and rice blast risk (KEI-2)

<ol class="steps">
<li><strong>Open "KEI-2 Habitat Health" and choose Location S.</strong>
KEI-2 looks at two things: life in the water, and life on land. The level on the card is always the worse of the two.
The land part uses the weather station, so it only exists at Location S. At the other locations KEI-2 shows the water part only.</li>
<li><strong>Tap "Local weather" (1) to see the weather station readings.</strong>
{% include shot.html id="kei2-weather" caption="(1) The Local weather tab. (2) Rice blast risk today. (3) Wind speed. (4) Where the data comes from: the Tancat de l'Estell station of Fundació Assut." %}
</li>
<li><strong>Read the rice blast risk (2).</strong>
Rice blast (<i>piricularia</i>) is a fungus that attacks rice. It spreads when the weather stays mild and very humid, or the leaves stay wet, for a long time.
The dashboard works this out from the weather station every hour. An hour counts as "favourable" for the fungus when the air is between 15 and 28 °C
and either the humidity is above 93% or the leaves are wet. The card shows the highest level reached that day:
<div class="levels">
  <div class="level l5"><b>0 · Low</b>The weather has not favoured the fungus.</div>
  <div class="level l2"><b>1 · Warning</b>More than 10 favourable hours in a row.</div>
  <div class="level l1"><b>2 · High</b>A warning together with at least 1 mm of rain, or warnings two days in a row, or more than 20 favourable hours in the last 3 days.</div>
</div>
</li>
</ol>

<div class="careful" markdown="1">
The rice blast index is an early warning worked out from the weather, not a check of your field. A high value does
not mean the disease is present, only that the weather may favour it. If it shows 1 or 2, walk your fields and follow the
advice of your agricultural technician. The Help page ("Parameter Descriptions") explains how the index is worked out.
</div>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 6</span>

## See the weather and water flow

<ol class="steps">
<li><strong>Open "Auxiliary Indicators".</strong>
These readings don't change the scores, but they help explain them.</li>
<li><strong>For weather, choose Location S.</strong>
You see the readings of the <b>Tancat de l'Estell</b> weather station, run by <b>Fundació Assut</b> and part of the AVAMET network of weather stations:
air pressure, sunlight, evapotranspiration (water lost from soil and plants), air temperature, leaf wetness, humidity, rain (1) and wind (2).
{% include shot.html id="aux-weather" caption="(1) Rain in the last 30 days. (2) The wind rose." %}
</li>
<li><strong>Read the wind rose (2).</strong>
It shows where the wind came <i>from</i>. The longer the dark wedge, the more days the wind blew from that side (N is north, S is south).</li>
<li><strong>For water flow, choose Global.</strong>
You see the lagoon's water level and how much water flows through the golas, the channels between the lagoon and the sea (1).
The data comes from the six gauging stations of the Júcar river authority (Confederación Hidrográfica del Júcar, CHJ), which publishes it once a day.
{% include shot.html id="aux-flow" caption="(1) Each card is one gauging station. Its name and the date CHJ last updated the data are under the title." %}
</li>
</ol>

<div class="tip" markdown="1">
A card that says "No data available" means the source sent nothing for that measurement in the last 30 days. It is not an error on your side.
</div>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 7</span>

## Tell us what you see (KEI-3)

<ol class="steps">
<li><strong>Choose Global, then scroll down on the main page to the poll.</strong>
The poll is open to anyone connected to l'Albufera. It is anonymous.
{% include shot.html id="poll" caption="(1) Give each question a mark from 1 to 5, or choose 'Don't know / No opinion'. (2) Say how you are connected to the area. (3) Send your answers." %}
</li>
<li><strong>Answer the questions from your own experience.</strong>
There are no right answers. What farmers and fishers see every day is exactly what the sensors can't measure.</li>
<li><strong>See what people think on the "KEI-3 Community Feedback" page.</strong>
This page is always about the whole lagoon, so it has no location buttons.
{% include shot.html id="kei3" caption="(1) The KEI-3 level. (2) The answers to each poll question. (3) One ring per question. (4) Who answered." %}
The page has two different kinds of information:
<ul>
<li><b>The ring charts (2, 3) are the public opinion itself.</b> There is one ring per question: <b>Q1</b> water quality, <b>Q2</b> the condition of habitats,
<b>Q3</b> how effective the restoration work is, and <b>Q4</b> whether the restoration work focuses on the right issues and areas.
Each colour is a mark people gave, from red (1, the worst) through orange, yellow and light green to dark green (5, the best).
Grey means "Don't know". <b>Avg</b> is the average mark. The charts count every answer received so far, online and on paper. To know what people think about one topic, read its ring.</li>
<li><b>The bar chart (4)</b> shows how the people who answered are connected to the area, for example residents, farmers or researchers.</li>
<li><b>The KEI-3 level (1) is not an opinion score.</b> It compares the average opinion over the last 30 days with the water and habitat levels (KEI-1 and KEI-2).
5 means opinion and measurements agree, lower means they differ. It does not tell you whether people are happy or not.</li>
</ul>
Help &amp; Documentation, section "How the KEIs Are Calculated", explains the exact KEI-3 calculation.
</li>
</ol>
</section>

<section class="part" markdown="1">
<span class="part-label">Part 8</span>

## Good to know

<ol class="steps">
<li><strong>Check when the data was last updated (1).</strong>
It's at the bottom of every page. Press <b>Refresh</b> (2) to load the newest data.
{% include shot.html id="footer" caption="(1) Last update. (2) Refresh. (3) Data use notice." %}
</li>
<li><strong>Read the data use notice (3).</strong>
The numbers are published automatically. Use them to stay informed, not as official information or for legal purposes.</li>
<li><strong>Look things up on the Help page.</strong>
"Help &amp; Documentation" in the menu has the full explanations behind this guide:
<ul>
<li><b>Which area a measurement covers</b>: the difference between a location and the open water the satellite looks at.</li>
<li><b>Data Sources</b>: where each kind of data comes from, who provides it, and under which licence.</li>
<li><b>How the KEIs Are Calculated</b>: how the measurements become the levels 1 to 5, for each indicator.</li>
<li><b>Parameter Descriptions</b>: what each measurement means.</li>
<li><b>Reference values and thresholds</b>: the exact reference value, warning threshold and critical threshold for each measurement, and their sources.</li>
</ul>
<a href="https://oberek.neverblink.eu/help">Open the Help page</a>.</li>
<li><strong>Everything is open.</strong>
All the data behind the dashboard can be downloaded for free, and the code that collects it and calculates the indicators is
<a href="https://github.com/NeverBlink-labs/oberek-code">published on GitHub</a>. The
<a href="{{ '/tutorials/live-data/' | relative_url }}">live-data</a> and <a href="{{ '/tutorials/research/' | relative_url }}">research</a>
tutorials show how to use them.</li>
</ol>
</section>

<div class="summary" markdown="1">
## 5 things to remember

1. **Pick your location** at the top: N, S, SW or Global. Weather and rice blast are at **S**, the poll and water flow at **Global**.
2. **5 is best, 1 is worst.** WARNING and CRITICAL mean a measurement crossed its warning or critical threshold.
3. **Watch the line**, not only the label: going down means getting worse.
4. **Tall single spikes** are often sensor errors.
5. **Rice blast 1 or 2**: walk your fields and ask your technician.

Exact thresholds and calculations: [Help & Documentation](https://oberek.neverblink.eu/help).
The data is provisional. Questions? Write to [contact@neverblink.eu](mailto:contact@neverblink.eu).
</div>

