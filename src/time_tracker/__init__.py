import flet
from .main import Application
from .db_operations import Database


def run():
    """Run the Time tracker application."""
    app = Application()
    flet.run(main=app.main)
