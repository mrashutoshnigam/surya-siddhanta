"""Install immutable DE440 at build/setup time; never called by the API.

Usage: python docker/fetch_ephemeris.py [--destination PATH]
"""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

SHA256 = "a4ce9bf9b3282becc9f4b2ac3cebe03a2ae7599981aabd7265fd8482fff7c4b5"
URL = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path,
        default=Path(os.environ.get("SS_EPHEMERIS_PATH", Path(__file__).resolve().parents[1] / "paper/data/kernels/de440.bsp")))
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.is_file() and digest(destination) == SHA256:
        print(f"Verified DE440: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="de440-", suffix=".download", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output, urlopen(URL, timeout=120) as response:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                output.write(chunk)
        if digest(temporary) != SHA256:
            raise SystemExit("DE440 checksum mismatch: the downloaded file was not installed")
        temporary.replace(destination)
        print(f"Installed verified DE440: {destination}")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
