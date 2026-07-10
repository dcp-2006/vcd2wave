"""Tests for VCD parser."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from vcd2wave.parser import parse_vcd, _parse_timescale_value

SAMPLE_VCD = """$date
\tWed Jun 24 2026
$end
$version
\tvcd2wave test
$end
$timescale
\t1ps
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


def _parse_text(text):
    """Helper: write text to tempfile, parse it, return results."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".vcd", delete=False) as f:
        f.write(text)
        tmp = f.name
    try:
        return parse_vcd(tmp)
    finally:
        Path(tmp).unlink()


def test_parse_vcd():
    signals, max_time, timescale = _parse_text(SAMPLE_VCD)
    assert len(signals) == 3
    assert "!" in signals  # clk
    assert '"' in signals  # rst_n
    assert "#" in signals  # sw
    assert max_time == 300
    assert signals["!"]["name"] == "top.clk"
    assert signals["!"]["width"] == 1
    assert signals["#"]["name"] == "top.sw"
    assert signals["#"]["width"] == 2
    # Timescale
    assert timescale["unit"] == "1ps"
    assert timescale["ps_per_unit"] == 1
    assert timescale["raw"] == "1ps"


def test_empty_vcd():
    signals, max_time, timescale = _parse_text(
        "$enddefinitions $end\n#0\n$dumpvars\n$end\n"
    )
    assert len(signals) == 0
    assert max_time == 0


def test_timescale_parsing():
    assert _parse_timescale_value("1ps") == ("1ps", 1)
    assert _parse_timescale_value("10ns") == ("10ns", 10000)
    assert _parse_timescale_value("100us") == ("100us", 100000000)
    assert _parse_timescale_value("1ms") == ("1ms", 1000000000)
    assert _parse_timescale_value("1s") == ("1s", 1000000000000)
    assert _parse_timescale_value("") == ("ps", 1)
    assert _parse_timescale_value("garbage") == ("ps", 1)


def test_timescale_from_vcd():
    vcd = "$timescale 10ns $end\n$enddefinitions $end\n"
    _, _, timescale = _parse_text(vcd)
    assert timescale["raw"] == "10ns"
    assert timescale["ps_per_unit"] == 10000
    assert timescale["unit"] == "10ns"


def test_scope_hierarchy():
    """Verify full hierarchy is preserved."""
    vcd = """$scope module top $end
$scope module uut $end
$var reg 1 ! clk $end
$upscope $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
0!
$end
"""
    signals, _, _ = _parse_text(vcd)
    assert signals["!"]["name"] == "top.uut.clk"


def test_vector_signal():
    vcd = """$scope module top $end
$var reg 4 $ data [3:0] $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
b1010 $
$end
#10
b1111 $
"""
    signals, max_time, _ = _parse_text(vcd)
    assert "$" in signals
    assert signals["$"]["width"] == 4
    assert max_time == 10
    assert len(signals["$"]["values"]) == 2
    assert signals["$"]["values"][0] == (0, "1010")
    assert signals["$"]["values"][1] == (10, "1111")


def test_xz_states():
    """X and Z states should be preserved."""
    vcd = """$scope module top $end
$var reg 1 ! sig $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
x!
$end
#10
z!
"""
    signals, _, _ = _parse_text(vcd)
    assert signals["!"]["values"][0] == (0, "x")
    assert signals["!"]["values"][1] == (10, "z")


def test_missing_file():
    import tempfile
    import os
    try:
        parse_vcd("/nonexistent/file.vcd")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_upscope_underflow():
    """Extra $upscope should not crash."""
    vcd = "$upscope $end\n$enddefinitions $end\n"
    try:
        _parse_text(vcd)
    except Exception as e:
        assert False, f"Extra $upscope caused exception: {e}"
