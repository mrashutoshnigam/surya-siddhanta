"""The chatbot's gnomon output must use Sun altitude and azimuth correctly."""

import json

import pytest

from suryasiddhanta.chatbot.tools import compute_gnomon_shadow


def test_gnomon_tool_reports_physical_sun_position_and_shadow():
    """April 9 at 06:00 UT in Ujjain puts the Sun high in the southeast."""
    result = json.loads(compute_gnomon_shadow(2024, 4, 9.25, 23.18, 75.78,
                                              utc_offset=0.0))

    assert result["sun_altitude"] == pytest.approx(69.80, abs=0.5)
    assert result["sun_azimuth"] == pytest.approx(139.68, abs=1.0)
    assert result["shadow_length"] == pytest.approx(4.42, abs=0.2)
    assert result["direction"] == "NW"
