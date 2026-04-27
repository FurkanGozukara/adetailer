from __future__ import annotations

import importlib.util
import subprocess
import sys
from importlib.metadata import version  # python >= 3.8

from packaging.version import parse

import_name = {"py-cpuinfo": "cpuinfo", "protobuf": "google.protobuf"}


def is_installed(
    package: str,
    min_version: str | None = None,
    max_version: str | None = None,
):
    name = import_name.get(package, package)
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError:
        return False

    if spec is None:
        return False

    if not min_version and not max_version:
        return True

    if not min_version:
        min_version = "0.0.0"
    if not max_version:
        max_version = "99999999.99999999.99999999"

    try:
        pkg_version = version(package)
        return parse(min_version) <= parse(pkg_version) <= parse(max_version)
    except Exception:
        return False


def run_pip(*args):
    subprocess.run([sys.executable, "-m", "pip", "install", *args], check=True)


def install():
    import tempfile
    import os

    # Install ultralytics and rich with numpy constraint
    simple_deps = [
        ("ultralytics", "8.3.75", None),
        ("rich", "13.0.0", None),
    ]

    pkgs = []
    for pkg, low, high in simple_deps:
        if not is_installed(pkg, low, high):
            if low and high:
                cmd = f"{pkg}>={low},<={high}"
            elif low:
                cmd = f"{pkg}>={low}"
            elif high:
                cmd = f"{pkg}<={high}"
            else:
                cmd = pkg
            pkgs.append(cmd)

    if pkgs:
        # Constrain numpy to prevent breaking scikit-image
        constraints = ["numpy<2.0.0"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(constraints))
            constraints_file = f.name
        
        try:
            run_pip("-c", constraints_file, *pkgs)
        finally:
            os.unlink(constraints_file)

    # Install mediapipe separately with --no-deps to avoid protobuf conflict
    # mediapipe works fine with protobuf 3.x at runtime despite the stated requirement
    if not is_installed("mediapipe", "0.10.13", "0.10.15"):
        run_pip("--no-deps", "mediapipe>=0.10.13,<=0.10.15")
        # Install mediapipe's actual required deps (excluding protobuf and opencv-contrib-python)
        # opencv-python is already installed by webui, opencv-contrib-python would pull numpy>=2
        mediapipe_deps = [
            "absl-py",
            "flatbuffers>=2.0",
            "sounddevice>=0.4.4",
            "cffi>=1.0",
        ]
        run_pip(*mediapipe_deps)


try:
    import launch

    skip_install = launch.args.skip_install
except Exception:
    skip_install = False

if not skip_install:
    install()
