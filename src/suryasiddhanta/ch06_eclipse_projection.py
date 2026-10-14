"""
Chapter 6: Projection of Eclipses (Parilekhadhikara)
==========================================================

Geometric projection of eclipses onto a diagram, computing:

  - **Valana** (deflection): combined ayana-valana (obliquity) and
    aksha-valana (observer latitude) giving the tilt of the ecliptic
    relative to the local horizon at the point of eclipse.
  - **Contact position angles**: direction of first/last contact on
    the disc of the eclipsed body.
  - **Path projection**: (x, y) locus of the eclipser's centre
    across the eclipsed disc.

Reference: SS Ch.6 v.1-24 (construction); valana is SS Ch.4 v.24-25.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union

from suryasiddhanta._types import LunarEclipse, SolarEclipse
from suryasiddhanta.ch01_mean_motions import from_julian_day
from suryasiddhanta.ch02_true_places import (
    normalize, compute, OBLIQUITY_DEGREES, sidereal_to_tropical, planet_latitude,
)
from suryasiddhanta.ch03_direction_place_time import (
    declination, ecliptic_to_equatorial, local_sidereal_time,
)


# ─────────────────────────────────────────────────────────────────
#  VALANA (DEFLECTION) — SS Ch.4 v.24-25 (used by the Ch.6 diagrams)
# ─────────────────────────────────────────────────────────────────

def ayana_valana(lon_deg: float,
                 obliquity: float = OBLIQUITY_DEGREES) -> float:
    """
    Ayana-valana: deflection due to obliquity of the ecliptic
    (SS Ch.4 v.25; the book's derivation, eq. 2).

    sin(av) = sin(obliquity) * cos(sayana longitude) / cos(declination)

    Zero at solstices (ecliptic parallel to equator).  North positive, as
    the book reckons it (north when longitude + 90 deg has northern
    declination).

    Args:
        lon_deg: Tropical (sayana) longitude of the eclipsed body

    Returns:
        Deflection angle in degrees
    """
    cos_dec = math.cos(math.radians(declination(lon_deg, obliquity)))
    if cos_dec < 1e-10:
        return 0.0
    sin_av = (math.sin(math.radians(obliquity))
              * math.cos(math.radians(lon_deg)) / cos_dec)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_av))))


def aksha_valana(hour_angle_deg: float, dec_deg: float,
                 lat_deg: float) -> float:
    """
    Aksha-valana: deflection due to the observer's latitude
    (SS Ch.4 v.24).

    sin(kv) = sin(lat) * sin(theta) / cos(dec), where theta is the
    "samaprota natamsha": tan(theta) = cos(dec) * |sin(H)| / cos(z), z being
    the body's zenith distance (equivalent to the book's
    tan(theta) = cos(agra) * tan(z)).  Checked against the book's lunar
    eclipse of Samvat 1981 at Kashi (theta 32d31', result 13d44').

    Args:
        hour_angle_deg: Hour angle, west positive
        dec_deg:        Declination of the eclipsed body
        lat_deg:        Observer latitude

    Returns:
        Deflection in degrees, north positive: a body in the west half
        of the sky gives a southern valana (book: "pashchim kapala").
    """
    lat_r = math.radians(lat_deg)
    dec_r = math.radians(dec_deg)
    h_r = math.radians(hour_angle_deg)
    cos_dec = math.cos(dec_r)
    if abs(cos_dec) < 1e-10:
        return 0.0
    cos_z = (math.sin(lat_r) * math.sin(dec_r)
             + math.cos(lat_r) * cos_dec * math.cos(h_r))
    theta = math.atan2(cos_dec * abs(math.sin(h_r)), cos_z)
    sin_kv = math.sin(lat_r) * math.sin(theta) / cos_dec
    kv = math.degrees(math.asin(max(-1.0, min(1.0, sin_kv))))
    return -kv if math.sin(h_r) > 0 else kv


def total_valana(lon_deg: float, hour_angle_deg: float,
                 lat_deg: float,
                 obliquity: float = OBLIQUITY_DEGREES,
                 lat_body_deg: float = 0.0) -> float:
    """
    Combined valana (ayana + aksha), north positive (SS Ch.4 v.25: add
    when the two are in the same direction, else take the difference).

    Args:
        lon_deg:        Tropical longitude of the eclipsed body
        hour_angle_deg: Hour angle of eclipsed body
        lat_deg:        Observer's geographic latitude
        lat_body_deg:   Ecliptic latitude of the eclipsed body

    Returns:
        Total deflection in degrees
    """
    av = ayana_valana(lon_deg, obliquity)
    _, dec = ecliptic_to_equatorial(lon_deg, lat_body_deg, obliquity)
    kv = aksha_valana(hour_angle_deg, dec, lat_deg)
    return av + kv


def _valana_at_eclipse(jd: float, lat_deg: float = 0.0,
                       lon_deg: float = 0.0,
                       body: str = "Sun") -> Tuple[float, float, float]:
    """
    Compute valana components at eclipse JD for the eclipsed (chhadya)
    body: the Sun in a solar eclipse, the Moon in a lunar one
    (SS Ch.4 v.24).  Returns (total, ayana, aksha).
    """
    y, m, d_frac = _jd_to_ymd(jd)
    pos = compute(body, y, m, d_frac)
    lon = sidereal_to_tropical(pos.true_longitude, jd)
    beta = planet_latitude(body, jd) / 60.0

    av = ayana_valana(lon)
    ra, dec = ecliptic_to_equatorial(lon, beta)
    lst = local_sidereal_time(jd, lon_deg)
    ha = normalize(lst - ra)
    if ha > 180:
        ha -= 360
    kv = aksha_valana(ha, dec, lat_deg)

    return av + kv, av, kv


def _jd_to_ymd(jd: float) -> Tuple[int, int, float]:
    y, m, d, frac = from_julian_day(jd)
    return y, m, d + frac


# ─────────────────────────────────────────────────────────────────
#  ECLIPSE GEOMETRY HELPERS
# ─────────────────────────────────────────────────────────────────

def _eclipse_radii(eclipse: Union[LunarEclipse, SolarEclipse]
                   ) -> Tuple[float, float, float, str]:
    """
    Extract geometric parameters from an eclipse result.
    Returns (eclipsed_r, eclipser_r, latitude_arcmin, body_name).
    """
    if isinstance(eclipse, LunarEclipse):
        # The Moon is the eclipsed (chhadya) body and the earth's shadow the
        # eclipser (chhadaka) -- SS Ch.6 v.2-12.
        return (eclipse.moon_diameter / 2,
                eclipse.shadow_diameter / 2,
                eclipse.moon_latitude,
                "Moon")
    else:
        return (eclipse.sun_diameter / 2,
                eclipse.moon_diameter / 2,
                eclipse.moon_latitude,
                "Sun")


# ─────────────────────────────────────────────────────────────────
#  CONTACT POINTS — SS Ch.6 v.4-12
# ─────────────────────────────────────────────────────────────────

def eclipse_contact_points(
    eclipse: Union[LunarEclipse, SolarEclipse],
    lat_deg: float = 0.0,
    lon_deg: float = 0.0,
) -> dict:
    """
    Position angles of first and last contact on the eclipsed disc.

    The position angle is measured from ecliptic north, clockwise,
    then rotated by the total valana to give the direction relative
    to the local vertical.

    Args:
        eclipse: LunarEclipse or SolarEclipse result
        lat_deg: Observer latitude (for aksha-valana)
        lon_deg: Observer longitude (for hour-angle)

    Returns:
        dict with keys: first_contact_pa, last_contact_pa,
        mid_eclipse_pa, valana, ayana_valana, aksha_valana
    """
    if not eclipse.is_eclipse:
        return {
            "first_contact_pa": None,
            "last_contact_pa": None,
            "mid_eclipse_pa": None,
            "valana": 0.0,
            "ayana_valana": 0.0,
            "aksha_valana": 0.0,
        }

    val_total, val_ay, val_ak = _valana_at_eclipse(
        eclipse.jd, lat_deg, lon_deg,
        body="Moon" if isinstance(eclipse, LunarEclipse) else "Sun")
    eclipsed_r, eclipser_r, lat_arcmin, _ = _eclipse_radii(eclipse)

    first_xy, last_xy, mid_xy = _contact_xy(
        eclipsed_r, eclipser_r, lat_arcmin,
        lunar=isinstance(eclipse, LunarEclipse))
    first_pa = normalize(val_total + math.degrees(math.atan2(*first_xy)))
    last_pa = normalize(val_total + math.degrees(math.atan2(*last_xy)))
    mid_pa = normalize(val_total + math.degrees(math.atan2(*mid_xy)))

    return {
        "first_contact_pa": round(first_pa, 2),
        "last_contact_pa": round(last_pa, 2),
        "mid_eclipse_pa": round(mid_pa, 2),
        "valana": round(val_total, 2),
        "ayana_valana": round(val_ay, 2),
        "aksha_valana": round(val_ak, 2),
    }


# ─────────────────────────────────────────────────────────────────
#  PATH PROJECTION — SS Ch.6 v.14-22 (simplified: straight chord)
# ─────────────────────────────────────────────────────────────────

def project_eclipse_path(
    eclipse: Union[LunarEclipse, SolarEclipse],
    n_points: int = 50,
) -> List[Tuple[float, float]]:
    """
    Project the eclipser's path across the eclipsed disc.

    The path is a straight chord.  Solar eclipses place the Moon at its
    signed latitude and begin on the west; lunar eclipses place the
    shadow opposite the Moon's latitude and begin on the east (v.4, 8).

    Coordinates in arcminutes, centred on the eclipsed body:
      x = along ecliptic (east positive)
      y = perpendicular to ecliptic (north positive)

    Args:
        eclipse:  LunarEclipse or SolarEclipse result
        n_points: Number of path samples (default 50)

    Returns:
        List of (x, y) tuples in arcminutes
    """
    if not eclipse.is_eclipse:
        return []

    eclipsed_r, eclipser_r, lat, _ = _eclipse_radii(eclipse)
    limit = eclipsed_r + eclipser_r
    discriminant = limit ** 2 - lat ** 2
    if discriminant < 0:
        return []

    x_max = math.sqrt(discriminant)
    lunar = isinstance(eclipse, LunarEclipse)
    points = []
    for i in range(n_points + 1):
        t = -1.0 + 2.0 * i / n_points
        x = round((-t if lunar else t) * x_max, 2)
        y = round(-lat if lunar else lat, 2)
        points.append((x, y))
    return points


# ─────────────────────────────────────────────────────────────────
#  CONTACT (x, y) COORDINATES
# ─────────────────────────────────────────────────────────────────

def _contact_xy(eclipsed_r: float, eclipser_r: float,
                lat: float, lunar: bool = False) -> Tuple[
                    Optional[Tuple[float, float]],
                    Optional[Tuple[float, float]],
                    Tuple[float, float]]:
    """
    Compute (x, y) of first contact, last contact, and mid-eclipse.
    Returns (first_xy, last_xy, mid_xy).
    """
    limit = eclipsed_r + eclipser_r
    disc = limit ** 2 - lat ** 2
    if disc < 0:
        return None, None, (0.0, -lat if lunar else lat)

    x_contact = math.sqrt(disc)
    y = round(-lat if lunar else lat, 2)
    first = (round(x_contact if lunar else -x_contact, 2), y)
    last = (round(-x_contact if lunar else x_contact, 2), y)
    mid = (0.0, y)
    return first, last, mid


# ─────────────────────────────────────────────────────────────────
#  DIAGRAM DATA — complete rendering package
# ─────────────────────────────────────────────────────────────────

@dataclass
class EclipseDiagram:
    """All geometric data needed to draw an eclipse diagram."""
    eclipse_type: str
    eclipsed_body: str
    eclipsed_radius: float
    eclipser_radius: float
    moon_latitude: float
    valana: float
    ayana_valana: float
    aksha_valana: float
    first_contact_pa: Optional[float]
    last_contact_pa: Optional[float]
    first_contact_xy: Optional[Tuple[float, float]]
    last_contact_xy: Optional[Tuple[float, float]]
    mid_eclipse_xy: Tuple[float, float]
    path: List[Tuple[float, float]]
    is_eclipse: bool

    def __str__(self) -> str:
        if not self.is_eclipse:
            return f"No eclipse to project ({self.eclipsed_body})"
        return (
            f"Eclipse Projection ({self.eclipse_type})\n"
            f"  Eclipsed body : {self.eclipsed_body} "
            f"(r={self.eclipsed_radius:.1f}′)\n"
            f"  Eclipser      : Moon (r={self.eclipser_radius:.1f}′)\n"
            f"  Moon latitude : {self.moon_latitude:.1f}′\n"
            f"  Valana        : {self.valana:.1f}° "
            f"(ayana={self.ayana_valana:.1f}°, "
            f"aksha={self.aksha_valana:.1f}°)\n"
            f"  1st contact PA: {self.first_contact_pa:.1f}°\n"
            f"  Last contact PA: {self.last_contact_pa:.1f}°\n"
            f"  Path points   : {len(self.path)}\n"
        )


def eclipse_diagram_data(
    eclipse: Union[LunarEclipse, SolarEclipse],
    lat_deg: float = 0.0,
    lon_deg: float = 0.0,
    n_points: int = 50,
) -> EclipseDiagram:
    """
    Assemble all geometric data for rendering an eclipse diagram.

    Combines valana, contact angles, contact coordinates, and
    the projected Moon path into a single data structure.

    Args:
        eclipse:  LunarEclipse or SolarEclipse
        lat_deg:  Observer latitude
        lon_deg:  Observer longitude
        n_points: Path resolution

    Returns:
        EclipseDiagram with all rendering data
    """
    eclipsed_r, eclipser_r, lat, body = _eclipse_radii(eclipse)
    contacts = eclipse_contact_points(eclipse, lat_deg, lon_deg)
    path = project_eclipse_path(eclipse, n_points)

    if eclipse.is_eclipse:
        first_xy, last_xy, mid_xy = _contact_xy(
            eclipsed_r, eclipser_r, lat, isinstance(eclipse, LunarEclipse))
    else:
        first_xy, last_xy, mid_xy = None, None, (0.0, 0.0)

    return EclipseDiagram(
        eclipse_type=eclipse.eclipse_type,
        eclipsed_body=body,
        eclipsed_radius=round(eclipsed_r, 2),
        eclipser_radius=round(eclipser_r, 2),
        moon_latitude=round(lat, 2),
        valana=contacts["valana"],
        ayana_valana=contacts["ayana_valana"],
        aksha_valana=contacts["aksha_valana"],
        first_contact_pa=contacts["first_contact_pa"],
        last_contact_pa=contacts["last_contact_pa"],
        first_contact_xy=first_xy,
        last_contact_xy=last_xy,
        mid_eclipse_xy=mid_xy,
        path=path,
        is_eclipse=eclipse.is_eclipse,
    )


# ─────────────────────────────────────────────────────────────────
#  OPTIONAL MATPLOTLIB DIAGRAM
# ─────────────────────────────────────────────────────────────────

def plot_eclipse(
    eclipse: Union[LunarEclipse, SolarEclipse],
    lat_deg: float = 0.0,
    lon_deg: float = 0.0,
    ax=None,
):
    """
    Draw an eclipse diagram using matplotlib (optional dependency).

    Shows the eclipsed disc, eclipser's path, and contact points.
    If matplotlib is not installed, raises ImportError.

    Args:
        eclipse:  LunarEclipse or SolarEclipse
        lat_deg:  Observer latitude
        lon_deg:  Observer longitude
        ax:       Optional matplotlib Axes to draw on

    Returns:
        matplotlib Axes object
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    diagram = eclipse_diagram_data(eclipse, lat_deg, lon_deg)

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))

    scale = max(diagram.eclipsed_radius, diagram.eclipser_radius) * 1.5

    eclipsed_circle = patches.Circle(
        (0, 0), diagram.eclipsed_radius,
        fill=False, edgecolor="gray", linewidth=2,
        label=diagram.eclipsed_body,
    )
    ax.add_patch(eclipsed_circle)

    eclipser_label = "Earth's shadow" if diagram.eclipsed_body == "Moon" else "Moon"

    if diagram.is_eclipse and diagram.mid_eclipse_xy:
        moon_circle = patches.Circle(
            diagram.mid_eclipse_xy, diagram.eclipser_radius,
            fill=False, edgecolor="blue", linewidth=1.5,
            linestyle="--", label=f"{eclipser_label} (mid)",
        )
        ax.add_patch(moon_circle)

    if diagram.path:
        xs = [p[0] for p in diagram.path]
        ys = [p[1] for p in diagram.path]
        ax.plot(xs, ys, "b-", linewidth=1, alpha=0.6, label=f"{eclipser_label} path")

    if diagram.first_contact_xy:
        ax.plot(*diagram.first_contact_xy, "ro", markersize=8,
                label="1st contact")
    if diagram.last_contact_xy:
        ax.plot(*diagram.last_contact_xy, "gs", markersize=8,
                label="Last contact")
    if diagram.mid_eclipse_xy and diagram.is_eclipse:
        ax.plot(*diagram.mid_eclipse_xy, "k^", markersize=8,
                label="Mid-eclipse")

    ax.set_xlim(-scale, scale)
    ax.set_ylim(-scale, scale)
    ax.set_aspect("equal")
    ax.axhline(0, color="lightgray", linewidth=0.5)
    ax.axvline(0, color="lightgray", linewidth=0.5)
    ax.set_xlabel("Along ecliptic (arcmin)")
    ax.set_ylabel("Perpendicular (arcmin)")
    ax.set_title(f"{diagram.eclipsed_body} Eclipse — {diagram.eclipse_type}")
    ax.legend(fontsize=8, loc="upper right")

    return ax
