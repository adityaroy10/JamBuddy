#!/usr/bin/env python3
"""Run AI Guitar Accompaniment. Use: python run.py"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

from app.main import main

if __name__ == "__main__":
    main()
