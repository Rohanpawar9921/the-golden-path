"""Launch the Streamlit clearance dashboard."""

from pathlib import Path
import sys
import os


def main() -> None:
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    from streamlit.web import cli as streamlit_cli

    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)
    app = project_root / "dashboard" / "clearance_queue.py"
    sys.argv = ["streamlit", "run", str(app)]
    raise SystemExit(streamlit_cli.main())


if __name__ == "__main__":
    main()
