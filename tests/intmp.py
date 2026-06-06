from logging import info
from os import environ
from pathlib import Path

def intmp(suffix, description):
    intmp.count += 1
    name = f"file{intmp.count}.{suffix}"
    path = intmp.tmpdir / name
    assert not path.exists()
    info(f"{path.name}: {description}")
    return path
intmp.count = 0
intmp.tmpdir = Path(environ['INTMP'])
