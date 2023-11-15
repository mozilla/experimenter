from pathlib import Path

import requests


def to_path(url: str, download_path: Path):
    """Download the given url to the given path."""
    with requests.get(url, stream=True) as rsp:
        rsp.raise_for_status()

        with download_path.open("wb") as f:
            for chunk in rsp.iter_content(chunk_size=8192):
                f.write(chunk)


def as_text(url: str) -> str:
    """Return the contents of the given URL."""
    rsp = requests.get(url)
    rsp.raise_for_status()

    return rsp.text
