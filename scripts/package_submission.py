"""Package an explicit allowlist; exclude environments, credentials and browser caches."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = [
    "app.py", "README.md", "NOTICE", "LICENSE.reference", "Dockerfile", ".dockerignore",
    ".gitignore", ".python-version", ".env.example", "pyproject.toml", "PRODUCT.md", "DESIGN.md",
    "requirements.txt", "requirements-dev.txt", "requirements-dev-only.txt",
    "requirements-windows.lock", "requirements-linux.lock", ".streamlit/config.toml",
    ".impeccable/design.json",
]
SOURCE_FOLDERS = ["src", "views", "cloud", "scripts", "tests", "docs"]


def submission_files() -> list[Path]:
    files = [ROOT / name for name in TOP_FILES]
    for folder in SOURCE_FOLDERS:
        files.extend(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts)
    files.extend(path for path in (ROOT / "models").iterdir() if path.is_file())
    files.extend(path for path in (ROOT / "artifacts").rglob("*") if path.is_file())
    files.append(ROOT / "data" / "raw" / "ai4i2020.csv")
    browser_evidence = ROOT / "output" / "playwright"
    captures = list(browser_evidence.glob("probability-*-final.png"))
    files.extend(captures or browser_evidence.glob("*-final.png"))
    files.extend(browser_evidence.glob("probability-*.csv"))
    files.extend(browser_evidence.glob("container-*-final.png"))
    files.extend(browser_evidence.glob("container-*.csv"))
    files.extend(browser_evidence.glob("cloudrun-*-final.png"))
    files.extend(browser_evidence.glob("cloudrun-*.csv"))
    return sorted(set(files))


def main() -> None:
    destination = ROOT.parent / "submission"
    destination.mkdir(exist_ok=True)
    archive_path = destination / "predictive-maintenance-control-center.zip"
    manifest = {}
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in submission_files():
            name = f"{ROOT.name}/{path.relative_to(ROOT).as_posix()}"
            archive.write(path, name)
            manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        reference = ROOT.parent / "reference" / "predictive-maintenance-ai4i"
        for path in sorted(reference.rglob("*")):
            if path.is_file() and ".git" not in path.relative_to(reference).parts:
                name = f"reference/predictive-maintenance-ai4i/{path.relative_to(reference).as_posix()}"
                archive.write(path, name)
                manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        archive.writestr("SHA256SUMS.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(archive_path) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise RuntimeError(f"Archive failed CRC validation: {bad_file}")
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (destination / "archive_sha256.txt").write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    print(f"{archive_path}\n{len(manifest)} files; {archive_path.stat().st_size:,} bytes; SHA256 {digest}")


if __name__ == "__main__":
    main()
