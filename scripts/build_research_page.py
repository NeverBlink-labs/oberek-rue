"""Rebuild the results shown on the research tutorial page from live data.

Runs tutorials/code/rederive_dashboard.ipynb against the public bucket (read-only)
and writes:

  _includes/research-notebook.md         text, code and results; included by tutorials/research.md
  assets/tutorials/img/research/*.png    the figures
  _data/research_capture.yml             when it was run

    pip install boto3 pandas matplotlib rdflib requests nbformat nbclient ipykernel
    python scripts/build_research_page.py

By default the notebook reads the metadata and ontology published in NeverBlink-labs/oberek-code.
Pass --metadata and --ontology to try local copies instead (for example a version not pushed yet).
"""
import argparse
import base64
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "tutorials/code/rederive_dashboard.ipynb"
INCLUDE = ROOT / "_includes/research-notebook.md"
IMG_DIR = ROOT / "assets/tutorials/img/research"
IMG_URL = "../../assets/tutorials/img/research"  # relative to /tutorials/research/
CAPTURE = ROOT / "_data/research_capture.yml"
FIGURE_ALT = {  # in the order the notebook draws them
    1: "Turbidity at the station: every reading as a grey line, with re-derived daily means and the dashboard's daily points on top",
    2: "Hourly average dissolved oxygen at the SouthWest and North stations, computed with SPARQL",
}


def run(metadata=None, ontology=None):
    nb = nbformat.read(NOTEBOOK, as_version=4)
    settings = nb.cells[1]
    original = settings.source
    if metadata:
        settings.source = re.sub(r"^METADATA = .*$", f'METADATA = r"{metadata}"', settings.source, flags=re.M)
    if ontology:
        settings.source = re.sub(r"^ONTOLOGY = .*$", f'ONTOLOGY = r"{ontology}"', settings.source, flags=re.M)
    with tempfile.TemporaryDirectory() as work:  # the notebook saves CSVs to its working folder
        NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": work}}).execute()
    settings.source = original  # show readers the settings they will use, not our local paths
    return nb


def to_markdown(nb):
    shutil.rmtree(IMG_DIR, ignore_errors=True)
    IMG_DIR.mkdir(parents=True)
    out, figure = [], 0
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            text = re.sub(r"^# .*\n+", "", cell.source)  # the page has its own title
            out.append(text)
            continue
        out.append(f"```python\n{cell.source}\n```")
        if cell.source.startswith("%pip"):
            continue  # pip's messages are not worth showing
        for o in cell.outputs:
            if o.output_type == "error":
                raise SystemExit(f"Notebook failed: {o.ename}: {o.evalue}")
            if o.output_type == "stream":
                if not o.text.strip():
                    continue
                out.append(f"```text\n{o.text.rstrip()}\n```")
                continue
            data = o.get("data", {})
            if "image/png" in data:
                figure += 1
                (IMG_DIR / f"figure-{figure}.png").write_bytes(base64.b64decode(data["image/png"]))
                alt = FIGURE_ALT.get(figure, f"Figure {figure}")
                out.append(f'<img src="{IMG_URL}/figure-{figure}.png" alt="{alt}" loading="lazy">')
            elif "text/html" in data:
                html = re.sub(r"<style.*?</style>", "", data["text/html"], flags=re.S).strip()
                out.append(f'<div class="table-scroll output">\n{html}\n</div>')
            elif "text/plain" in data:
                out.append(f"```text\n{data['text/plain']}\n```")
    body = "\n\n".join(out)
    INCLUDE.write_text("{% raw %}\n" + body + "\n{% endraw %}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--metadata", help="local metadata file instead of the published one")
    p.add_argument("--ontology", help="local ontology file instead of the published one")
    a = p.parse_args()
    started = datetime.now(timezone.utc)
    local = lambda path: Path(path).resolve() if path else None
    to_markdown(run(local(a.metadata), local(a.ontology)))
    CAPTURE.write_text(f'captured: "{started:%Y-%m-%d %H:%M} UTC"\n')
    print(f"wrote {INCLUDE.relative_to(ROOT)} and {len(list(IMG_DIR.glob('*.png')))} figures")
