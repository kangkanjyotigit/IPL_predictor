"""Thin runner that uses the canonical app from app.py"""
from app import app

if __name__ == '__main__':
    app.run(debug=True)
