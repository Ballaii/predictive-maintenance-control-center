"""Execute the untouched reference notebook in an isolated working directory."""
import json
import shutil
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT.parent / "reference" / "predictive-maintenance-ai4i"


def main() -> None:
    notebook = nbformat.read(REFERENCE / "notebook" / "predictive_maintenance.ipynb", as_version=4)
    destination = ROOT / "artifacts" / "reference_reproduction"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ai4i-reference-") as directory:
        work = Path(directory)
        (work / "data").mkdir()
        shutil.copy2(ROOT / "data" / "raw" / "ai4i2020.csv", work / "data")
        client = NotebookClient(
            notebook, timeout=600, kernel_name="python3",
            resources={"metadata": {"path": str(work)}},
        )
        client.execute()
        nbformat.write(notebook, destination / "executed.ipynb")
        for path in (work / "assets").iterdir():
            shutil.copy2(path, destination / path.name)
    summary = {
        "reference_commit": "ef563b06272bb6ad583e1719fa416174409f359f",
        "execution": "Original code cells executed unchanged; isolated cwd and official CSV.",
        "environment": "Project Python 3.11 environment; numerical pins match reference core.",
        "warning": "Reference test-set threshold selection retained for reproduction only.",
    }
    (destination / "provenance.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print((destination / "metrics_summary.csv").read_text())


if __name__ == "__main__":
    main()
