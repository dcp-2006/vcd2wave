"""Tests for VCD parser."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from vcd2wave.parser import parse_vcd


SAMPLE_VCD = """$date
	Wed Jun 24 2026
$end
$version
	vcd2wave test
$end
$timescale
	1ps
$end
$scope module top $end
$var reg 1 ! clk $end
$var reg 1 " rst_n $end
$var reg 2 # sw [1:0] $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
0!
0"
b00 #
$end
#10
1!
#20
0!
#30
1!
b01 #
#300
1"
b10 #
"""


def test_parse_vcd():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".vcd", delete=False) as f:
        f.write(SAMPLE_VCD)
        tmp = f.name

    try:
        signals, max_time = parse_vcd(tmp)
        assert len(signals) == 3
        assert "!" in signals  # clk
        assert '"' in signals  # rst_n
        assert "#" in signals  # sw
        assert max_time == 300
        assert signals["!"]["name"] == "top.clk"
        assert signals["!"]["width"] == 1
    finally:
        Path(tmp).unlink()


def test_empty_vcd():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".vcd", delete=False) as f:
        f.write("$enddefinitions $end\n#0\n$dumpvars\n$end\n")
        tmp = f.name

    try:
        signals, max_time = parse_vcd(tmp)
        assert len(signals) == 0
    finally:
        Path(tmp).unlink()
