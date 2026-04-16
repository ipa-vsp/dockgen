import shutil
import subprocess


def detect():
    if _command_ok("nvidia-smi"):
        return "nvidia"
    if _command_ok("rocm-smi"):
        return "amd"
    return "none"


def _command_ok(cmd):
    path = shutil.which(cmd)
    if not path:
        return False
    try:
        result = subprocess.run(
            [path],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0
