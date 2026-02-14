import flet
from .main import Application
from .db_operations import Database

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("time-tracker")
except PackageNotFoundError:
    __version__ = "0.1.0"  # Fallback for development


def run():
    """Run the Time tracker application."""
    app = Application()
    flet.run(main=app.main)
