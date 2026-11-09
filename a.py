"""
Flask app that lets you download the workspace source code as a ZIP file.
Run:
   pip install flask
   python source_downloader.py
Then open http://127.0.0.1:5050 and click "Download source (.zip)",
or request http://127.0.0.1:5050/download directly.
"""
import io
import os
import zipfile
from datetime import datetime
from pathlib import Path
from flask import Flask, abort, render_template_string, send_file
# Defaults to the folder this script lives in, so it works on any machine.
WORKSPACE_DIR = Path(
   os.environ.get("WORKSPACE_DIR", Path(__file__).resolve().parent)
).resolve()
# Folders and files that are not source code and would bloat the archive.
EXCLUDED_DIRS = {
   ".git", "__pycache__", "node_modules", ".venv", "venv",
   ".idea", ".vscode", ".pytest_cache", ".mypy_cache", "dist", "build",
}
EXCLUDED_FILES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
app = Flask(__name__)
INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Workspace Source Download</title>
<style>
   body { font-family: system-ui, sans-serif; margin: 3rem auto; max-width: 560px; padding: 0 1rem; }
   a.button { display: inline-block; padding: 0.7rem 1.2rem; background: #2563eb; color: #fff;
              border-radius: 6px; text-decoration: none; }
   code { background: #f2f2f2; padding: 0.1rem 0.3rem; border-radius: 4px; }
</style>
</head>
<body>
<h1>Workspace source code</h1>
<p>Folder: <code>{{ folder }}</code></p>
<p><a class="button" href="download">Download source (.zip)</a></p>
</body>
</html>
"""

def should_include(path: Path) -> bool:
   """Return True if the file should go into the archive."""
   if path.is_symlink() or not path.is_file():
       return False
   if path.name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
       return False
   return not any(part in EXCLUDED_DIRS for part in path.relative_to(WORKSPACE_DIR).parts)

def build_source_zip(root: Path) -> io.BytesIO:
   """Create the ZIP archive in memory and return it rewound to the start."""
   buffer = io.BytesIO()
   with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
       for dirpath, dirnames, filenames in os.walk(root):
           # Prune excluded directories in place so os.walk skips them.
           dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
           for name in sorted(filenames):
               path = Path(dirpath) / name
               if should_include(path):
                   arcname = Path(root.name) / path.relative_to(root)
                   archive.write(path, arcname=str(arcname))
   buffer.seek(0)
   return buffer

@app.route("/")
def index():
   return render_template_string(INDEX_HTML, folder=str(WORKSPACE_DIR))

# The extra route covers proxies that forward the full path (e.g. /proxy/8080/download).
@app.route("/download")
@app.route("/<path:prefix>/download")
def download(prefix=None):
   if not WORKSPACE_DIR.is_dir():
       abort(404, description=f"Workspace not found: {WORKSPACE_DIR}")
   timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
   zip_name = f"{WORKSPACE_DIR.name}-source-{timestamp}.zip"
   return send_file(
       build_source_zip(WORKSPACE_DIR),
       mimetype="application/zip",
       as_attachment=True,
       download_name=zip_name,
   )

if __name__ == "__main__":
   # Hosted IDEs (e.g. the examly proxy) forward to a fixed port and need 0.0.0.0.
   app.run(
       host="127.0.0.1",
       port="8081",
       debug=False,
   )