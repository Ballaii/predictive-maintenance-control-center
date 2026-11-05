import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CloudConfig:
    project: str
    dataset: str
    location: str

    @classmethod
    def from_environment(cls) -> "CloudConfig | None":
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        if not project:
            return None
        dataset = os.getenv("BQ_DATASET", "maintenance_demo")
        location = os.getenv("BQ_LOCATION", "EU")
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project):
            raise ValueError("GOOGLE_CLOUD_PROJECT is not a valid project ID.")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,100}", dataset):
            raise ValueError("BQ_DATASET must be a simple BigQuery dataset identifier.")
        return cls(project, dataset, location)

    @property
    def dataset_id(self) -> str:
        return f"{self.project}.{self.dataset}"
