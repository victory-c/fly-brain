"""Builds and loads lif_kernel.c, the CPU fast path of brain/engine.py.

    lib = kernel.load()      # ctypes handle, or None when there is nothing to load

The C file is compiled once per machine with gcc and OpenMP (-march=native, so the login VM and the compute
node each get their own build) into ~/.cache/fly_brain (FLY_BRAIN_CACHE to move it). load() returns None, and
Engine falls back to its torch ops, when FLY_BRAIN_KERNEL=0, when there is no gcc, or when the build fails.
Threads: OMP_NUM_THREADS, else every core the process may use.
"""
import ctypes
import hashlib
import os
import platform
import subprocess
import tempfile
from pathlib import Path

SRC = Path(__file__).with_name("lif_kernel.c")
FLAGS = ["-O3", "-march=native", "-fopenmp", "-ffp-contract=off", "-fPIC", "-shared"]
_lib = False  # False: not tried yet; None: unavailable


def _machine():
    """What -march=native depends on: the architecture and the CPU's feature flags."""
    try:
        with open("/proc/cpuinfo") as f:
            flags = next((line for line in f if line.startswith("flags")), "")
    except OSError:
        flags = platform.processor()
    return platform.machine() + flags


def _build():
    source = SRC.read_bytes()
    key = hashlib.sha256(source + " ".join(FLAGS).encode() + _machine().encode()).hexdigest()[:16]
    cache = Path(os.environ.get("FLY_BRAIN_CACHE", Path.home() / ".cache" / "fly_brain"))
    so = cache / f"lif_kernel_{key}.so"
    if not so.exists():
        cache.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=cache, suffix=".so")  # build aside, then rename: jobs may start together
        os.close(fd)
        try:
            subprocess.run(["gcc", *FLAGS, "-o", tmp, str(SRC)], check=True, capture_output=True, timeout=120)
            os.replace(tmp, so)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    lib = ctypes.CDLL(str(so))
    p, i64, f32 = ctypes.c_void_p, ctypes.c_int64, ctypes.c_float
    lib.lif_dense.restype = i64
    lib.lif_dense.argtypes = [p, p, p, p, i64, ctypes.c_int32, f32, f32, f32, f32, p]
    lib.lif_deliver.restype = None
    lib.lif_deliver.argtypes = [p, p, p, i64, i64, p, p, p, p, f32]
    return lib


def load():
    global _lib
    if _lib is False:
        _lib = None
        if os.environ.get("FLY_BRAIN_KERNEL", "1") != "0":
            try:
                _lib = _build()
            except (OSError, subprocess.SubprocessError, AttributeError) as err:
                print(f"brain/kernel.py: C kernel unavailable ({type(err).__name__}), using torch ops")
    return _lib
