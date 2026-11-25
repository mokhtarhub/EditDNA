# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""python run.py <command> ...   (same as python -m editdna, works from any folder)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from editdna.__main__ import main
main()
