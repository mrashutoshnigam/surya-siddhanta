"""
Shared test fixtures for suryasiddhanta test suite.

Key dates used throughout testing:
- Kali epoch: Feb 18, 3102 BCE (JD 588465.5)
- Brahmagupta era: Jan 1, 628 CE
- Ayanamsha zero: 499 CE
- Modern: April 9, 2024
"""

import pytest

KALI_EPOCH_JD = 588465.5


@pytest.fixture
def jd_kali_epoch():
    """Julian Day at Kali Yuga epoch (Feb 18, 3102 BCE)."""
    return KALI_EPOCH_JD


@pytest.fixture
def jd_628():
    """Julian Day for Jan 1, 628 CE (Brahmagupta era)."""
    # JD for Jan 1, 628 CE (Julian calendar)
    # Computed: 1952062.5
    return 1952062.5


@pytest.fixture
def jd_499():
    """Julian Day for Jan 1, 499 CE (ayanamsha zero year)."""
    return 1904907.5


@pytest.fixture
def jd_2024():
    """Julian Day for April 9, 2024 (modern test date)."""
    return 2460410.5


@pytest.fixture
def ujjain_location():
    """Ujjain (SS reference meridian) latitude and longitude."""
    return (23.18, 75.77)


@pytest.fixture
def all_planets():
    """List of all seven classical planets."""
    return ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
