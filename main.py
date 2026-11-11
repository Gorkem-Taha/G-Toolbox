"""G-Toolbox entry point, kept at the project root for compatibility.

    python main.py [--lan] [--port N] [--no-browser]
    uvicorn main:app

The application itself lives in the ``gtoolbox`` package:
``gtoolbox/app.py`` builds the FastAPI app from the routers in ``gtoolbox/routers``.
"""

from gtoolbox.app import app, run_server

__all__ = ["app", "run_server"]  # `uvicorn main:app` and the launchers use these


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="G-Toolbox server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--lan", action="store_true", help="allow paired devices on the local network")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    run_server(port=args.port, open_browser=not args.no_browser)
