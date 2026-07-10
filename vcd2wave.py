#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vcd2wave - Convert VCD waveform files to interactive HTML visualizations.

Usage:
    vcd2wave input.vcd [-o output.html] [--no-open] [--timescale UNIT]
"""
import sys
import os

# Enable running directly from source without pip install
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vcd2wave import main

if __name__ == "__main__":
    main()
