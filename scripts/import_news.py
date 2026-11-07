"""Scheduled editorial import; never publishes automatically."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app
from services.news_import import import_cisa

if __name__ == '__main__':
    with app.app_context():
        print(f'Imported {import_cisa()} new drafts. Review in Publishing Studio.')
