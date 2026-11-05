from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "ai4i2020.csv"
ARTIFACTS = ROOT / "artifacts"
MODELS = ROOT / "models"
SEED = 42
DEFAULT_POLICY = "high_precision"
POLICY_LABELS = {"high_precision": "High precision", "balanced": "Balanced F1"}
TARGET = "Machine failure"
CATEGORY = "Type"
NUMERIC = [
    "Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]",
    "Torque [Nm]", "Tool wear [min]",
]
FEATURES = [CATEGORY, *NUMERIC]
FLAGS = ["TWF", "HDF", "PWF", "OSF", "RNF"]
COLUMNS = ["UDI", "Product ID", *FEATURES, TARGET, *FLAGS]
DATA_URL = (
    "https://archive.ics.uci.edu/static/public/601/"
    "ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip"
)
DATA_SHA256 = "dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_BATCH_ROWS = 10000
PHYSICAL_BOUNDS = {
    "Air temperature [K]": (200, 500),
    "Process temperature [K]": (200, 600),
    "Rotational speed [rpm]": (1, 10000),
    "Torque [Nm]": (0.01, 500),
    "Tool wear [min]": (0, 1000),
}
