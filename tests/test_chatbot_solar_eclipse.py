"""The chatbot must distinguish an omitted place from a place at 0°, 0°."""

import json

from suryasiddhanta.chatbot.tools import compute_solar_eclipse


def test_zero_zero_is_a_valid_topocentric_place():
    geocentric = json.loads(compute_solar_eclipse(2024, 4, 8))
    at_origin = json.loads(compute_solar_eclipse(2024, 4, 8, latitude=0, longitude=0))

    assert "locally_visible" not in geocentric
    assert isinstance(at_origin["locally_visible"], bool)
    assert isinstance(at_origin["sun_altitude_deg"], float)
