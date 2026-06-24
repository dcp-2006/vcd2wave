#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vcd2wave - VCD波形文件转HTML可视化工具
把ModelSim/Vivado/iverilog生成的VCD转成浏览器能看的波形图

Usage:
    python vcd2wave.py <input.vcd> [output.html]
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vcd2wave import main

if __name__ == "__main__":
    main()
