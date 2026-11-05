"""Record trusted local inference for a Windows/Linux parity check without retraining."""
import argparse
import json
import platform
from pathlib import Path

import pandas as pd
import sklearn

from src.config import ARTIFACTS, FEATURES, POLICY_LABELS
from src.inference import Predictor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    predictor = Predictor.load()
    history = pd.read_csv(ARTIFACTS / "historical_probabilities.csv")
    result = {
        "python": platform.python_version(), "platform": platform.system(),
        "scikit_learn": sklearn.__version__, "model": predictor.metadata["selected_model"],
        "version": predictor.metadata["version"], "model_sha256": predictor.metadata["model_sha256"],
        "observations": len(history), "udi": history.UDI.tolist(), "policies": {},
    }
    for policy in POLICY_LABELS:
        predictions = predictor.predict(history[FEATURES], policy)
        result["policies"][policy] = {
            "threshold": predictor.policy(policy)["threshold"],
            "probabilities": predictions.failure_probability.tolist(),
            "classifications": predictions.elevated_risk.tolist(),
            "elevated_count": int(predictions.elevated_risk.sum()),
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
    print(json.dumps({"platform": result["platform"], "observations": len(history),
                      "model": result["model"], "output": str(output),
                      "elevated": {key: value["elevated_count"]
                                   for key, value in result["policies"].items()}}, indent=2))


if __name__ == "__main__":
    main()
