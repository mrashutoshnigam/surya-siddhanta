"""Curated learning copy, separated from calculated positions and the SS text."""
from __future__ import annotations

from .explorer_schemas import BodyInfo, Source

NASA = Source(label="NASA planetary fact sheet", url="https://nssdc.gsfc.nasa.gov/planetary/factsheet/")
SS1 = Source(label="Surya Siddhanta, Chapter 1", url="/book/1")
SS2 = Source(label="Surya Siddhanta, Chapter 2", url="/book/2")
SS12 = Source(label="Surya Siddhanta, Chapter 12", url="/book/12")

# Signed sidereal rotation periods, diameters, orbital periods and obliquities:
# NASA fact sheet. These are teaching constants, not an attitude ephemeris.
_DATA = [
    ("Sun", "Surya", "star", "#f6bd61", 609.12, 7.25, 1392700, None,
     "Our star lights and warms the worlds around it. Its glowing surface is hot gas, not solid ground.",
     "The historical model calculates the Sun’s direction around Earth, with a manda correction to its mean motion.", "sun"),
    ("Mercury", "Budha", "planet", "#b7a99b", 1407.6, .034, 4879, 88,
     "A small, rocky world with a heavily cratered surface. It travels closest to the Sun.",
     "Mercury’s mean-place convention follows the mean Sun; its corrections give its Earth-centered direction.", "mercury"),
    ("Venus", "Shukra", "planet", "#dfc296", -5832.5, 177.4, 12104, 224.7,
     "Thick clouds hide this rocky world. It rotates very slowly, in the opposite sense to most planets.",
     "Venus uses manda and sighra corrections. Its historical mean-place convention is not a modern solar orbit.", "venus_atmosphere"),
    ("Earth", "Prithvi", "planet", "#7ebcf0", 23.9345, 23.4, 12756, 365.2,
     "Our home has oceans, land, and a protective atmosphere. Its turning gives us day and night in modern astronomy.",
     "Earth is the stationary positional centre of this historical model. The spinning texture is a modern illustration.", "earth_daymap"),
    ("Moon", "Chandra", "moon", "#c6c9cd", 655.7, 6.7, 3475, 27.3,
     "Earth’s natural satellite reflects sunlight. It turns once in about the time it takes to go around Earth.",
     "The Moon’s true longitude and latitude are calculated from its mean motion, apogee and node.", "moon"),
    ("Mars", "Mangala", "planet", "#d38362", 24.6, 25.2, 6792, 687,
     "A rocky world with a rusty surface. Its day is a little longer than Earth’s.",
     "Manda and sighra corrections change Mars’s mean direction. Its calculated longitude can temporarily move backward.", "mars"),
    ("Jupiter", "Brihaspati", "planet", "#d2b291", 9.9, 3.1, 142984, 4331,
     "The largest planet is a gas giant. Its visible bands are cloud systems, not a solid surface.",
     "Jupiter moves slowly through the zodiac; Chapter 2 corrects its mean longitude to a true longitude.", "jupiter"),
    ("Saturn", "Shani", "planet", "#dfc991", 10.7, 26.7, 120536, 10747,
     "A gas giant surrounded by bright rings made of countless icy particles.",
     "Saturn is the outermost classical planet represented here. Its long period gives a slow mean motion.", "saturn"),
    ("Uranus", "", "planet", "#a5d9df", -17.2, 97.8, 51118, 30589,
     "An ice giant with a strongly tilted axis. It rolls around the Sun almost on its side.", None, "uranus"),
    ("Neptune", "", "planet", "#5a84d7", 16.1, 28.3, 49528, 59800,
     "A distant ice giant with an atmosphere and powerful winds. Its year is much longer than ours.", None, "neptune"),
]


def body_catalog():
    result = {}
    for name, sanskrit, kind, color, rotation, tilt, diameter, period, intro, historical, texture in _DATA:
        sources = [NASA]
        if name == "Sun":
            sources = [Source(label="NASA Sun facts", url="https://science.nasa.gov/sun/facts/")]
        if historical:
            sources += [SS1, SS2, SS12]
        result[name] = BodyInfo(id=name, sanskrit=sanskrit, kind=kind,
            models=["historical", "modern"] if historical else ["modern"],
            introduction=intro, historical=historical, rotation_hours=rotation,
            tilt_deg=tilt, diameter_km=diameter, orbital_days=period, color=color,
            texture=f"/textures/{texture}.jpg", sources=sources)
    for name in ("Rahu", "Ketu"):
        result[name] = BodyInfo(id=name, sanskrit=name, kind="node", models=["historical"],
            color="#a69ce0" if name == "Rahu" else "#d5a7cb",
            introduction="A direction where the Moon’s path crosses the ecliptic, not a physical globe.",
            historical="Rahu is the Moon’s ascending node. Ketu is drawn opposite it as a derived convention; the text does not calculate Ketu separately.",
            sources=[SS1, SS2])
    return result


BODIES = body_catalog()
HISTORICAL = ["Earth", "Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]
MODERN = ["Sun", "Mercury", "Venus", "Earth", "Moon", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
