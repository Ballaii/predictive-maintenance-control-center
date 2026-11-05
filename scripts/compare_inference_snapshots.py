"""Compare recorded host/container inference and write a bounded verification report."""
import argparse
import json
from pathlib import Path

import numpy as np


def compare_snapshots(host: dict, container: dict) -> dict:
    for key in ["model", "version", "model_sha256", "scikit_learn", "observations", "udi"]:
        if host[key] != container[key]:
            raise ValueError(f"Host/container snapshot mismatch: {key}")
    if set(host["policies"]) != set(container["policies"]):
        raise ValueError("Host and container expose different classification policies.")
    results = {}
    for policy, reference in host["policies"].items():
        actual = container["policies"][policy]
        if reference["threshold"] != actual["threshold"]:
            raise ValueError(f"Classification threshold differs for {policy}.")
        np.testing.assert_allclose(reference["probabilities"], actual["probabilities"], rtol=0, atol=1e-12)
        np.testing.assert_array_equal(reference["classifications"], actual["classifications"])
        difference = np.asarray(reference["probabilities"]) - np.asarray(actual["probabilities"])
        results[policy] = {"max_absolute_probability_difference": float(np.abs(difference).max()),
                           "classifications_identical": True, "elevated_count": actual["elevated_count"]}
    return {"status": "passed", "observations": host["observations"],
            "model": host["model"], "model_sha256": host["model_sha256"],
            "host_python": host["python"], "container_python": container["python"],
            "host_platform": host["platform"], "container_platform": container["platform"],
            "policies": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--container", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    host = json.loads(args.host.read_text(encoding="utf-8"))
    container = json.loads(args.container.read_text(encoding="utf-8"))
    report = compare_snapshots(host, container)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
