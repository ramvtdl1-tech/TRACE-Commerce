"""Build a source-only release; never traverse arbitrary workspace files."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "README.md", "LICENSE", "requirements.txt", ".env.example", ".env.hackathon.example", ".gitignore",
    ".dockerignore", "Dockerfile", "compose.yaml", "render.yaml", "catalog.json",
    "postman/trace-commerce.postman_collection.json",
    "postman/trace-commerce.postman_environment.json", "postman/README.md",
)
DIRECTORIES = {
    "commerce": {".py"}, "static": {".html", ".js", ".css", ".svg"},
    "tests": {".py"}, "scripts": {".py"}, "docs": {".md"},
    ".github/workflows": {".yml", ".yaml"},
}


def sources():
    for name in FILES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing or unsafe required source file: " + name)
        yield path
    for folder, extensions in DIRECTORIES.items():
        base = ROOT / folder
        if not base.is_dir() or base.is_symlink():
            raise ValueError("Missing or unsafe source directory: " + folder)
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(base)
            if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                continue
            if path.is_file() and path.suffix in extensions:
                if path.is_symlink() or ROOT not in path.resolve().parents:
                    raise ValueError("Symlink source rejected")
                yield path


def main():
    paths = sorted(set(sources()))
    archive = ROOT / "dist" / "trace-commerce-deploy.zip"
    archive.parent.mkdir(exist_ok=True)
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in paths:
            bundle.write(path, path.relative_to(ROOT))
    print(str(archive))
    print(str(len(paths)) + " source files; no runtime data or credentials included.")
    print("SHA256 " + hashlib.sha256(archive.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
