"""Write a portable notebook that calls the same local scientific implementation."""
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.metadata.kernelspec = {
        "display_name": "Python 3.11", "language": "python", "name": "python3",
    }
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            "# AI4I condition classifier: local / Workbench\n\n"
            "Educational synthetic data, no future failure horizon. This notebook reuses the "
            "same modules, split seed and selection procedure as the local application. "
            "No cloud resources or BigQuery jobs are created by these cells. Use Python 3.11. "
            "Install requirements-dev.txt in that kernel before running. In Workbench, upload "
            "the project without credentials or .venv and select the project root below."
        ),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport os\nimport sys\n\n"
            "candidates = [Path.cwd(), Path.cwd().parent]\n"
            "project_root = next((p for p in candidates if (p / 'src' / 'train.py').exists()), None)\n"
            "if project_root is None:\n"
            "    raise RuntimeError('Open this notebook inside the uploaded project/cloud directory.')\n"
            "os.chdir(project_root)\nsys.path.insert(0, str(project_root))\n"
            "print('Project:', project_root, '\\nPython:', sys.version)\n"
            "if sys.version_info[:2] != (3, 11):\n"
            "    raise RuntimeError('Use a Python 3.11 kernel for the locked experiment.')"
        ),
        nbformat.v4.new_code_cell(
            "from src.data_loader import download_dataset, load_dataset, dataset_report\n"
            "from src.config import DATA_PATH\n"
            "if not DATA_PATH.exists():\n    download_dataset()\n"
            "dataset = load_dataset()\nreport = dataset_report(dataset)\n"
            "print({key: report[key] for key in ['rows', 'target_counts', 'label_inconsistencies']})\n"
            "dataset.head()"
        ),
        nbformat.v4.new_markdown_cell(
            "## Preprocessing, fitting and validation-only selection\n\n"
            "The same module creates a 60/20/20 stratified split, scaled/OHE LR and OHE RF, "
            "three-fold training-internal calibration candidates, validation-selected thresholds "
            "and the frozen model selection before test evaluation. Existing artifacts are never "
            "silently retrained. For a new experiment, archive models/ and artifacts/ before starting."
        ),
        nbformat.v4.new_code_cell(
            "from src.train import split_dataset\nfrom src.preprocessing import model_candidates\n"
            "splits = split_dataset(dataset)\n"
            "print({name: {'rows': len(part), 'failures': int(part['Machine failure'].sum())} "
            "for name, part in splits.items()})\nmodel_candidates()"
        ),
        nbformat.v4.new_code_cell(
            "import subprocess\nfrom src.config import MODELS\n"
            "if not (MODELS / 'metadata.json').exists():\n"
            "    subprocess.run([sys.executable, '-m', 'src.train'], check=True)\n"
            "else:\n    print('Loading the completed original experiment; no retraining performed.')\n"
            "if not (MODELS / 'probability_metadata.json').exists():\n"
            "    subprocess.run([sys.executable, '-m', 'src.probability_profile'], check=True)\n"
            "else:\n    print('Loading the persisted calibrated probability profile.')"
        ),
        nbformat.v4.new_code_cell(
            "import json\nimport pandas as pd\nfrom src.config import ARTIFACTS\n"
            "results = json.loads((ARTIFACTS / 'evaluation.json').read_text())\n"
            "metrics = ['accuracy', 'precision', 'recall', 'f1', 'average_precision', 'roc_auc', 'brier_score']\n"
            "comparison = pd.DataFrame({name: {key: result['test'][key] for key in metrics} "
            "for name, result in results.items()}).T\ncomparison"
        ),
        nbformat.v4.new_code_cell(
            "from src.inference import Predictor\nfrom src.config import FEATURES\n"
            "predictor = Predictor.load()\nprint(predictor.metadata['selected_model'], "
            "predictor.metadata['threshold'], predictor.metadata['score_kind'])\n"
            "print('Classification policies:', predictor.metadata['policies'])\n"
            "predictor.predict(dataset[FEATURES].head())"
        ),
        nbformat.v4.new_code_cell(
            "subprocess.run([sys.executable, 'scripts/export_reports.py'], check=True)\n"
            "print('Exported artifacts/test_metrics.csv, artifacts/figures/, docs/evaluation_report.md')\n"
            "print('Model, schema and metadata:', MODELS)"
        ),
        nbformat.v4.new_markdown_cell(
            "## Interpretation and cleanup\n\n"
            "Test results belong to the frozen local methodology, not the reference experiment. "
            "The original winner is uncalibrated RF; the dashboard uses the separate calibrated RF "
            "probability profile. Both policy thresholds use validation evidence, and profile metrics "
            "reuse the previously inspected test partition. Small failure counts, synthetic "
            "data and missing external validation limit interpretation. Cloud execution remains "
            "unverified until actually run in Workbench. Close/delete any paid notebook resources "
            "and inspect retained disks after the assessment."
        ),
    ]
    path = ROOT / "cloud" / "vertex_training.ipynb"
    nbformat.write(notebook, path)
    print(path)


if __name__ == "__main__":
    main()
