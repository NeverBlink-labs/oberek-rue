"""Take the dashboard screenshots used by tutorials/dashboard.md.

Opens the live dashboard in a headless browser (read-only: it only looks at
pages), saves one PNG per shot to assets/tutorials/img/dashboard/ and writes
the numbered marker positions to _data/screenshots.yml. The page draws the
markers on top of the images, so after re-running this script the markers
follow the new layout.

    pip install playwright pyyaml pillow
    playwright install chromium
    python scripts/capture_screenshots.py              # all shots
    python scripts/capture_screenshots.py kei-cards    # only these shots
    python scripts/capture_screenshots.py --lang es    # Spanish dashboard (es or va)

To add a shot: add an entry to SHOTS, run the script, then put
{% include shot.html id="<id>" %} on the page.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from PIL import Image
from playwright.sync_api import sync_playwright

DASHBOARD = "https://oberek.neverblink.eu"
ROOT = Path(__file__).resolve().parent.parent
LANGS = ("en", "es", "va")

VIEWPORTS = {
    "desktop": {"viewport": {"width": 1440, "height": 900}, "device_scale_factor": 1},
    "phone": {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True},
}
LOCATION_LABELS = {
    "en": {"Global": "Global", "North": "Location N", "South": "Location S", "SouthWest": "Location SW"},
    "es": {"Global": "Global", "North": "Ubicación N", "South": "Ubicación S", "SouthWest": "Ubicación SO"},
    "va": {"Global": "Global", "North": "Ubicació N", "South": "Ubicació S", "SouthWest": "Ubicació SO"},
}
MONTHS = {
    "es": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(),
    "va": "gener febrer març abril maig juny juliol agost setembre octubre novembre desembre".split(),
}

# Each shot:
#   route, location, viewport  which page to open, and how
#   click      optional selector to click first (e.g. a tab)
#   clip       selector of the area to keep; omit to keep the whole screen
#   pad        extra pixels kept around the clipped area: one number, or [top, right, bottom, left] (default 8)
#   max_height cut the area off below this many pixels
#   markers    selectors to number 1, 2, 3…. By default the marker sits on the centre of
#              the element. Add ":after" (just after its text), ":left-out", ":right-out"
#              or ":above" (next to it) so the marker doesn't cover what it points at.
#              Start with "?" if the element may not exist (the marker is then left out).
# Use SouthWest for water data, South for weather and rice blast (the only weather station,
# Tancat de l'Estell, belongs to South), Global for the flow gauges and the community poll results.
SHOTS = {
    "overview": {
        "route": "/", "location": "Global", "viewport": "desktop",
        "alt": "The OBEREK dashboard main page: menu on the left, location buttons at the top, three indicator cards and the start of the community poll",
        "markers": [".sidebar-nav-item >> nth=0 >> span:after", ".location-tabs:right-out",
                    ".kei-card >> nth=0 >> .kei-card-name:after", ".poll-form-title:after", ".lang-select:right-out"],
    },
    "phone": {
        "route": "/", "location": "SouthWest", "viewport": "phone",
        "alt": "The dashboard on a phone: language menu at the top, location buttons, indicator cards, and the menu bar at the bottom",
        "markers": [".topbar-lang:left-out", ".location-tabs:above", ".bottom-nav"],
    },
    "locations-map": {
        "route": "/help", "location": "Global", "viewport": "desktop",
        "clip": ".help-section:has(.help-section-title:text-is('Monitored Locations'))", "max_height": 760,
        "alt": "Map of l'Albufera with the three monitoring locations and the flow gauging stations",
    },
    "kei-cards": {
        "route": "/", "location": "SouthWest", "viewport": "desktop", "clip": ".kei-cards-grid",
        "alt": "The three indicator cards: water quality, habitat health and community feedback, each with a level and a small chart",
        "markers": [".kei-card >> nth=0 >> .kei-card-name:after", ".kei-card >> nth=0 >> .kei-badge:left-out",
                    ".kei-card >> nth=0 >> .kei-card-chart"],
    },
    "kei1-trend": {
        "route": "/kei-1", "location": "SouthWest", "viewport": "desktop",
        "clip": ".chart-section >> nth=0",
        "alt": "The water quality page: a line chart of the score over the last 30 days, with the current level in the corner",
        "markers": [".chart-section >> nth=0 >> .kei-badge:left-out", ".chart-section >> nth=0 >> .chart-section-title:after"],
    },
    "kei1-cards": {
        "route": "/kei-1", "location": "SouthWest", "viewport": "desktop", "clip": ".param-cards-grid",
        "alt": "Six measurement cards for the SouthWest water sensors, each with a status label, the latest value and a chart",
        "markers": [".param-card >> nth=0 >> .param-card-name:after", ".param-card >> nth=0 >> .status-badge:left-out",
                    ".param-card >> nth=0 >> .param-card-value:after", "?.param-card:has(.status-badge--Warning, .status-badge--Critical) >> nth=0 >> .status-badge:left-out"],
    },
    "kei1-satellite": {
        "route": "/kei-1", "location": "SouthWest", "viewport": "desktop",
        "click": ".source-tab:has-text('Satellite')", "clip": ".kei-map-split",
        "alt": "Satellite measurements for the SouthWest area next to a coloured map of the same area",
        "markers": [".kei-constituent-cards .param-card >> nth=0 >> .status-badge:left-out",
                    ".heatmap-layer-btn >> nth=0:left-out", ".map-container"],
    },
    "kei2-weather": {
        "route": "/kei-2", "location": "South", "viewport": "desktop",
        "click": ".source-tab:has-text('Local weather')", "clip": ".main-content", "pad": 0, "max_height": 960,
        "alt": "The habitat health page for the South location, showing the rice blast risk and wind speed cards",
        "markers": [".source-tab:has-text('Local weather'):right-out", ".param-card:has-text('Rice Blast') >> .param-card-value:after",
                    ".param-card:has-text('Wind speed') >> .param-card-value:after",
                    ".param-card:has-text('Wind speed') >> .param-card-source:after"],
    },
    "aux-weather": {
        "route": "/auxiliary", "location": "South", "viewport": "desktop",
        "clip": "h2:text-is('Local weather stations') >> xpath=..", "max_height": 1400,
        "alt": "Weather cards from the Tancat de l'Estell station: pressure, sunlight, evapotranspiration, temperature, leaf wetness, humidity, rain and a wind rose",
        "markers": [".param-card:has-text('Precipitation') >> .param-card-name:after",
                    ".param-card:has-text('Wind direction') >> .param-card-name:after"],
    },
    "aux-flow": {
        "route": "/auxiliary", "location": "Global", "viewport": "desktop",
        "clip": "h2:text-is('Flow Gauging Stations') >> xpath=..", "max_height": 672,
        "alt": "Flow rate cards for the gauging stations on the channels between the lagoon and the sea",
        "markers": [".param-card:has-text('08A02') >> nth=0 >> .param-card-source:after"],
    },
    "poll": {
        "route": "/", "location": "Global", "viewport": "desktop", "clip": ".poll-form",
        "alt": "The community poll: five questions with answers from 1 to 5, a list of connections to the area, and a submit button",
        "markers": [".poll-question >> nth=0 >> .poll-question-label:after", ".poll-options:right-out",
                    ".poll-form .btn-primary:right-out"],
    },
    "kei3": {
        "route": "/kei-3", "location": "Global", "viewport": "desktop", "clip": ".main-content", "pad": 0, "max_height": 1180,
        "alt": "The community feedback page: the KEI-3 level over time, one ring chart per poll question, and a bar chart of who answered",
        "markers": [".chart-section >> nth=0 >> .kei-badge:left-out",
                    ".card-title:text-is('Community Polls Statistics'):after",
                    ".donut-item >> nth=0 >> .donut-label:after",
                    ".card-title:text-is('Surveys Statistics'):after"],
    },
    "footer": {
        "route": "/", "location": "Global", "viewport": "desktop", "clip": ".app-footer", "pad": [36, 0, 0, 0],
        "alt": "The bottom of every page: last update time, refresh button, data use notice and contact",
        "markers": [".app-footer-updated:above", ".app-footer-refresh:above", ".app-footer-notice:above"],
    },
}

# Text that the selectors above look for, as the dashboard shows it in each language.
TEXT = {
    "es": {"Monitored Locations": "Ubicaciones monitorizadas", "Satellite": "Satélite",
           "Local weather": "Meteorología local", "Rice Blast": "Piriculariosis", "Wind speed": "Velocidad del viento",
           "Local weather stations": "Estaciones meteorológicas locales", "Precipitation": "Precipitación",
           "Wind direction": "Dirección del viento", "Flow Gauging Stations": "Estaciones de Aforo",
           "Community Polls Statistics": "Estadísticas de las encuestas a la comunidad",
           "Surveys Statistics": "Estadísticas de las encuestas"},
    "va": {"Monitored Locations": "Ubicacions monitoritzades", "Satellite": "Satèl·lit",
           "Local weather": "Meteorologia local", "Rice Blast": "Piriculariosi", "Wind speed": "Velocitat del vent",
           "Local weather stations": "Estacions meteorològiques locals", "Precipitation": "Precipitació",
           "Wind direction": "Direcció del vent", "Flow Gauging Stations": "Estacions d'Aforament",
           "Community Polls Statistics": "Estadístiques de les enquestes a la comunitat",
           "Surveys Statistics": "Estadístiques de les enquestes"},
}

ALT = {
    "es": {
        "overview": "Página principal del panel OBEREK: menú a la izquierda, botones de ubicación arriba, las tres tarjetas de indicadores y el inicio de la encuesta de la comunidad",
        "phone": "El panel en un móvil: menú de idioma arriba, botones de ubicación, tarjetas de indicadores y la barra de menú abajo",
        "locations-map": "Mapa de l'Albufera con las tres ubicaciones monitorizadas y las estaciones de aforo",
        "kei-cards": "Las tres tarjetas de indicadores: calidad del agua, salud del hábitat y percepción de la comunidad, cada una con su nivel y un pequeño gráfico",
        "kei1-trend": "La página de calidad del agua: gráfico de línea de la puntuación de los últimos 30 días, con el nivel actual en la esquina",
        "kei1-cards": "Seis tarjetas de medición de los sensores de agua de la ubicación Suroeste, cada una con su estado, el último valor y un gráfico",
        "kei1-satellite": "Mediciones por satélite del área Suroeste junto a un mapa en color de la misma área",
        "kei2-weather": "La página de salud del hábitat de la ubicación Sur, con las tarjetas del riesgo de piriculariosis y la velocidad del viento",
        "aux-weather": "Tarjetas meteorológicas de la estación Tancat de l'Estell: presión, irradiancia, evapotranspiración, temperatura, humectación foliar, humedad, precipitación y una rosa de los vientos",
        "aux-flow": "Tarjetas de caudal de las estaciones de aforo de las golas, los canales entre el lago y el mar",
        "poll": "La encuesta de la comunidad: preguntas con respuestas del 1 al 5, una lista de vínculos con la zona y el botón de envío",
        "kei3": "La página de percepción de la comunidad: el nivel del KEI-3 en el tiempo, un gráfico de anillo por pregunta y un gráfico de barras de quién respondió",
        "footer": "La parte inferior de cada página: última actualización, botón de actualizar, aviso sobre el uso de los datos y contacto",
    },
    "va": {
        "overview": "Pàgina principal del tauler OBEREK: menú a l'esquerra, botons d'ubicació a dalt, les tres targetes d'indicadors i l'inici de l'enquesta de la comunitat",
        "phone": "El tauler en un mòbil: menú d'idioma a dalt, botons d'ubicació, targetes d'indicadors i la barra de menú a baix",
        "locations-map": "Mapa de l'Albufera amb les tres ubicacions monitoritzades i les estacions d'aforament",
        "kei-cards": "Les tres targetes d'indicadors: qualitat de l'aigua, salut de l'hàbitat i percepció de la comunitat, cadascuna amb el seu nivell i un xicotet gràfic",
        "kei1-trend": "La pàgina de qualitat de l'aigua: gràfic de línia de la puntuació dels últims 30 dies, amb el nivell actual en la cantonada",
        "kei1-cards": "Sis targetes de mesurament dels sensors d'aigua de la ubicació Sud-oest, cadascuna amb el seu estat, l'últim valor i un gràfic",
        "kei1-satellite": "Mesuraments per satèl·lit de l'àrea Sud-oest al costat d'un mapa en color de la mateixa àrea",
        "kei2-weather": "La pàgina de salut de l'hàbitat de la ubicació Sud, amb les targetes del risc de piriculariosi i la velocitat del vent",
        "aux-weather": "Targetes meteorològiques de l'estació Tancat de l'Estell: pressió, irradiància, evapotranspiració, temperatura, humectació foliar, humitat, precipitació i una rosa dels vents",
        "aux-flow": "Targetes de cabal de les estacions d'aforament de les goles, els canals entre el llac i la mar",
        "poll": "L'enquesta de la comunitat: preguntes amb respostes de l'1 al 5, una llista de vincles amb la zona i el botó d'enviament",
        "kei3": "La pàgina de percepció de la comunitat: el nivell del KEI-3 en el temps, un gràfic d'anell per pregunta i un gràfic de barres de qui ha respost",
        "footer": "La part de baix de cada pàgina: última actualització, botó d'actualitzar, avís sobre l'ús de les dades i contacte",
    },
}


def localise(selector, lang):
    """Swap the English text inside a selector's quotes for the dashboard's text in `lang`."""
    words = TEXT.get(lang, {})
    return re.sub(r"'([^']*)'", lambda m: '"%s"' % words[m.group(1)] if m.group(1) in words else m.group(0), selector)


def paths(lang):
    """Where the images and marker data go: English at the top level, other languages beside it."""
    if lang == "en":
        return ROOT / "assets/tutorials/img/dashboard", ROOT / "_data/screenshots.yml"
    return ROOT / f"assets/tutorials/img/dashboard/{lang}", ROOT / f"_data/screenshots_{lang}.yml"


def capture_date(lang):
    now = datetime.now(timezone.utc)
    if lang == "en":
        return now.strftime("%-d %B %Y")
    month = MONTHS[lang][now.month - 1]
    joiner = "d'" if lang == "va" and month[0] in "ao" else "de "
    return f"{now.day} {joiner}{month} de {now.year}"


def box(page, selector):
    handle = page.locator(selector).first
    handle.wait_for(state="visible", timeout=15000)
    handle.scroll_into_view_if_needed()
    return handle.bounding_box()


ANCHORS = ("after", "left-out", "right-out", "above")
GAP = 26  # px between a marker and the element it points at


def marker_point(page, spec):
    """Where to draw a marker, in viewport pixels. See the SHOTS comment for the options."""
    selector, where = spec, "center"
    head, _, tail = spec.rpartition(":")
    if tail in ANCHORS:
        selector, where = head, tail
    b = box(page, selector)
    cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    if where == "after":  # just past the end of the element's text
        end = page.locator(selector).first.evaluate("""el => {
            const r = document.createRange(); r.selectNodeContents(el);
            const rects = [...r.getClientRects()]; const last = rects[rects.length - 1];
            return last ? [last.right, last.top + last.height / 2] : null; }""")
        return (end[0] + GAP, end[1]) if end else (b["x"] + b["width"] + GAP, cy)
    if where == "left-out":
        return b["x"] - GAP, cy
    if where == "right-out":
        return b["x"] + b["width"] + GAP, cy
    if where == "above":
        return cx, b["y"] - GAP
    return cx, cy


def settle(page):
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass  # a slow map tile or chart request should not stop the capture
    try:
        page.wait_for_function("!document.querySelector('.skeleton')", timeout=20000)
    except Exception:
        pass  # some cards stay empty when there is no data; take the picture anyway
    page.wait_for_timeout(2500)  # charts and map tiles finish drawing


def capture(browser, shot_id, shot, lang, img_dir, today):
    ctx = browser.new_context(**VIEWPORTS[shot["viewport"]])
    ctx.add_init_script(f"localStorage.setItem('oberek.location', '{shot['location']}');"
                        f"localStorage.setItem('oberek_lang', '{lang}');")
    page = ctx.new_page()
    page.goto(DASHBOARD + shot["route"], wait_until="domcontentloaded", timeout=60000)
    settle(page)
    if shot.get("click"):
        page.locator(localise(shot["click"], lang)).first.click()
        settle(page)

    # Page coordinates, so that scrolling does not matter.
    scroll = lambda: page.evaluate("[window.scrollX, window.scrollY]")
    if shot.get("clip"):
        b = box(page, localise(shot["clip"], lang))
        sx, sy = scroll()
        pad = shot.get("pad", 8)
        top, right, bottom, left = pad if isinstance(pad, list) else [pad] * 4
        area = {"x": b["x"] + sx - left, "y": b["y"] + sy - top,
                "width": b["width"] + left + right, "height": b["height"] + top + bottom}
        full_page = True
    else:
        vp = VIEWPORTS[shot["viewport"]]["viewport"]
        page.evaluate("window.scrollTo(0, 0)")
        area = {"x": 0, "y": 0, "width": vp["width"], "height": vp["height"]}
        full_page = False
    if shot.get("max_height"):
        area["height"] = min(area["height"], shot["max_height"])
    # Keep the area inside the page, or the edges come out cut off.
    page_w, page_h = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
    area["x"], area["y"] = max(area["x"], 0), max(area["y"], 0)
    area["width"] = min(area["width"], page_w - area["x"])
    area["height"] = min(area["height"], page_h - area["y"])

    markers = []
    for n, spec in enumerate(shot.get("markers", []), start=1):
        optional = spec.startswith("?")
        try:
            x, y = marker_point(page, localise(spec.lstrip("?"), lang))
        except Exception:
            if optional:
                continue
            raise
        sx, sy = scroll()
        px, py = x + sx - area["x"], y + sy - area["y"]
        markers.append({"n": n, "x": round(100 * px / area["width"], 2), "y": round(100 * py / area["height"], 2)})
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)

    path = img_dir / f"{shot_id}.png"
    page.screenshot(path=str(path), clip=area, full_page=full_page)
    Image.open(path).convert("RGB").quantize(colors=256).save(path, optimize=True)  # much smaller files
    ctx.close()
    return {
        "file": "/" + str(path.relative_to(ROOT)),
        "alt": ALT.get(lang, {}).get(shot_id, shot["alt"]),
        "viewport": shot["viewport"],
        "width": round(area["width"]),
        "height": round(area["height"]),
        "location": LOCATION_LABELS[lang][shot["location"]],
        "captured": today,
        "markers": markers,
    }


def main(lang, only):
    img_dir, data_file = paths(lang)
    img_dir.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(data_file.read_text()) if data_file.exists() else {}
    today = capture_date(lang)
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for shot_id, shot in SHOTS.items():
            if only and shot_id not in only:
                continue
            try:
                data[shot_id] = capture(browser, shot_id, shot, lang, img_dir, today)
                print(f"ok   {shot_id}")
            except Exception as e:  # keep going; report at the end
                failed.append(shot_id)
                print(f"FAIL {shot_id}: {e}")
        browser.close()
    header = "# Written by scripts/capture_screenshots.py. Do not edit by hand.\n"
    data_file.write_text(header + yaml.safe_dump(data, sort_keys=True, allow_unicode=True))
    if failed:
        sys.exit(f"{len(failed)} shot(s) failed: {', '.join(failed)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    lang = "en"
    if "--lang" in args:
        i = args.index("--lang")
        lang = args[i + 1]
        del args[i:i + 2]
    if lang not in LANGS:
        sys.exit(f"--lang must be one of: {', '.join(LANGS)}")
    main(lang, set(args))
