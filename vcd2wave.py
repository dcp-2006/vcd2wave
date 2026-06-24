#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vcd2wave - Convert VCD waveform files to interactive HTML visualizations.

Usage:
    python vcd2wave.py <input.vcd> [output.html]
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vcd2wave import main

if __name__ == "__main__":
    main()
