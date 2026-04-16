import os
import sys
from pathlib import Path

from dockgen.probes import display as display_probe
from dockgen.probes import gpu as gpu_probe
from dockgen.probes import vscode as vscode_probe
from dockgen.ros import ROS_BASE_IMAGES


def run(defaults=None):
    d = defaults or {}
    a = {}
    try:
        _step_0_container_name(a, d)
        _step_1_output(a, d)
        _step_2_ros(a, d)
        _step_3_base_image(a, d)
        _step_3b_dockerfile(a, d)
        _step_4a_gpu(a, d)
        _step_4b_display(a, d)
        _step_4c_network(a, d)
        _step_5_user_env(a, d)
        _step_6_volumes(a, d)
        _step_7_startup(a, d)
        _step_8_devcontainer(a, d)
        _step_9_advanced(a, d)
    except (KeyboardInterrupt, EOFError):
        print("\naborted.", file=sys.stderr)
        sys.exit(130)
    return a


# ---------- helpers ----------

def _section(title):
    print(f"\n── {title} ──")


def _ask(prompt, default=None, choices=None):
    hint = ""
    if choices:
        hint = f" [{'/'.join(choices)}]"
    if default is not None and default != "":
        hint += f" ({default})"
    while True:
        raw = input(f"  {prompt}{hint}: ").strip()
        if not raw:
            if default is not None:
                return default
            print("    (required)")
            continue
        if choices and raw not in choices:
            print(f"    choose from: {', '.join(choices)}")
            continue
        return raw


def _ask_bool(prompt, default=False):
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"  {prompt} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def _ask_kv(prompt, existing):
    print(f"  {prompt} (KEY=VALUE, blank to finish)")
    for k, v in existing.items():
        print(f"    • {k}={v}")
    result = dict(existing)
    while True:
        raw = input("    + ").strip()
        if not raw:
            break
        if "=" not in raw:
            print("      expected KEY=VALUE")
            continue
        k, v = raw.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def _ask_list(prompt, existing):
    print(f"  {prompt} (one per line, blank to finish)")
    for item in existing:
        print(f"    • {item}")
    result = list(existing)
    while True:
        raw = input("    + ").strip()
        if not raw:
            break
        result.append(raw)
    return result


def _ask_select(prompt, items, default_selected=None):
    if not items:
        return list(default_selected or [])
    selected = set(default_selected or [])
    print(f"  {prompt}")
    for i, item in enumerate(items, 1):
        mark = "*" if item in selected else " "
        print(f"    [{mark}] {i:>2}. {item}")
    print(
        "    (comma-separated numbers to toggle, 'all', 'none',"
        " or blank to keep current)"
    )
    raw = input("    > ").strip().lower()
    if not raw:
        return sorted(selected)
    if raw == "all":
        return list(items)
    if raw == "none":
        return []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            idx = int(part) - 1
        except ValueError:
            continue
        if 0 <= idx < len(items):
            item = items[idx]
            if item in selected:
                selected.discard(item)
            else:
                selected.add(item)
    return sorted(selected)


def _detect_tz():
    tz = Path("/etc/timezone")
    if tz.exists():
        try:
            return tz.read_text().strip()
        except OSError:
            pass
    return "UTC"


# ---------- steps ----------

def _step_0_container_name(a, d):
    _section("Container name")
    default = d.get("service_name") or Path(os.getcwd()).name or "dev"
    a["service_name"] = _ask("Container / service name?", default=default)


def _step_1_output(a, d):
    _section("Output format")
    a["output_format"] = _ask(
        "Generate compose, devcontainer, or both?",
        default=d.get("output_format", "compose"),
        choices=["compose", "devcontainer", "both"],
    )


def _step_2_ros(a, d):
    _section("ROS")
    a["ros_distro"] = _ask(
        "ROS distro?",
        default=d.get("ros_distro", "none"),
        choices=["jazzy", "humble", "iron", "noetic", "rolling", "none"],
    )


def _step_3_base_image(a, d):
    _section("Base image")
    distro = a["ros_distro"]
    if distro != "none":
        default = d.get("base_image") or ROS_BASE_IMAGES.get(distro, "")
    else:
        default = d.get("base_image", "ubuntu:24.04")
    a["base_image"] = _ask("Base image?", default=default)


def _step_3b_dockerfile(a, d):
    _section("Custom Dockerfile")
    default_custom = d.get("dockerfile") == "custom"
    custom = _ask_bool(
        "Build a custom Dockerfile on top of the base image?",
        default=default_custom,
    )
    if not custom:
        a["dockerfile"] = "none"
        a["dev_user"] = d.get("dev_user", "")
        a["apt_packages"] = d.get("apt_packages", [])
        a["pip_packages"] = d.get("pip_packages", [])
        a["user_workspace"] = d.get("user_workspace", "")
        return
    a["dockerfile"] = "custom"
    a["dev_user"] = _ask("Non-root user name?", default=d.get("dev_user") or "dev")
    a["apt_packages"] = _ask_list("Extra apt packages", d.get("apt_packages", []))
    a["pip_packages"] = _ask_list("Pip packages", d.get("pip_packages", []))
    create_ws = _ask_bool(
        f"Create a workspace folder inside /home/{a['dev_user']}?",
        default=d.get("user_workspace") is not None,
    )
    if create_ws:
        a["user_workspace"] = _ask(
            "Workspace folder name?",
            default=d.get("user_workspace") or "ws",
        )
    else:
        a["user_workspace"] = ""


def _step_4a_gpu(a, d):
    _section("GPU")
    detected = gpu_probe.detect()
    if detected == "none":
        print("  no GPU tooling detected (nvidia-smi / rocm-smi)")
    else:
        print(f"  detected: {detected}")
    a["gpu"] = _ask(
        "GPU runtime?",
        default=d.get("gpu", detected),
        choices=["none", "nvidia", "amd"],
    )


def _step_4b_display(a, d):
    _section("Display / GUI")
    detected = display_probe.detect()
    if detected == "none":
        print("  no DISPLAY or WAYLAND_DISPLAY in the environment")
    else:
        print(f"  detected: {detected}")
    display_default = d.get("display") or (detected if detected != "none" else "x11")
    a["display"] = _ask(
        "GUI forwarding?",
        default=display_default,
        choices=["none", "x11", "wayland", "vnc"],
    )
    if a["display"] == "vnc":
        print("  note: VNC sidecar rendering is planned; compose will omit it for now.")


def _step_4c_network(a, d):
    _section("Network")
    if a["ros_distro"] != "none":
        print("  note: ROS 2 DDS discovery usually needs host networking.")
        net_default = d.get("network", "host")
    else:
        net_default = d.get("network", "bridge")
    a["network"] = _ask(
        "Network mode?",
        default=net_default,
        choices=["host", "bridge", "custom"],
    )
    if a["network"] == "custom":
        a["network_name"] = _ask(
            "Custom network name?",
            default=d.get("network_name", "dockgen_net"),
        )
    else:
        a["network_name"] = d.get("network_name", "")


def _step_5_user_env(a, d):
    _section("User & environment")
    a["passthrough_uid"] = _ask_bool(
        "Pass host UID/GID into container?",
        default=d.get("passthrough_uid", True),
    )
    a["timezone"] = _ask("Timezone?", default=d.get("timezone", _detect_tz()))
    a["env"] = _ask_kv("Extra env vars", d.get("env", {}))


def _step_6_volumes(a, d):
    _section("Volumes")
    cwd = os.getcwd()
    user = a.get("dev_user") or "dev"
    user_ws = a.get("user_workspace") or ""
    container_mount = f"/home/{user}/{user_ws}" if user_ws else "/workspace"
    a["container_mount"] = d.get("container_mount", container_mount)
    a["workspace_mount"] = _ask_bool(
        f"Mount current directory ({cwd}) into {a['container_mount']}?",
        default=d.get("workspace_mount", True),
    )
    a["extra_mounts"] = _ask_list(
        "Additional bind mounts (HOST:CONTAINER)",
        d.get("extra_mounts", []),
    )


def _step_7_startup(a, d):
    _section("Startup command")
    a["startup"] = _ask(
        "Startup command?",
        default=d.get("startup", "tail -f /dev/null"),
    )


def _step_8_devcontainer(a, d):
    if a["output_format"] not in ("devcontainer", "both"):
        a["post_create"] = d.get("post_create", "")
        a["vscode_extensions"] = d.get("vscode_extensions", [])
        return
    _section("Devcontainer extras")
    a["post_create"] = _ask("postCreateCommand?", default=d.get("post_create", ""))
    installed = vscode_probe.list_installed()
    prior = d.get("vscode_extensions", [])
    if installed:
        print(f"  ({len(installed)} extensions found in ~/.vscode/extensions)")
        a["vscode_extensions"] = _ask_select(
            "Select VSCode extensions to include",
            installed,
            default_selected=prior,
        )
    else:
        print("  no local VSCode extensions found; enter manually")
        a["vscode_extensions"] = _ask_list(
            "VSCode extensions (e.g. ms-python.python)",
            prior,
        )


def _step_9_advanced(a, d):
    _section("Advanced options")
    if not _ask_bool("Show advanced options?", default=False):
        a["privileged"] = d.get("privileged", False)
        a["ipc_host"] = d.get("ipc_host", a["ros_distro"] != "none")
        a["cap_add"] = d.get("cap_add", [])
        a["cap_drop"] = d.get("cap_drop", [])
        return
    a["privileged"] = _ask_bool(
        "Privileged mode?", default=d.get("privileged", False)
    )
    ipc_default = d.get("ipc_host", a["ros_distro"] != "none")
    a["ipc_host"] = _ask_bool(
        "ipc: host (shared memory — recommended for ROS 2)?",
        default=ipc_default,
    )
    a["cap_add"] = _ask_list("Linux capabilities to add", d.get("cap_add", []))
    a["cap_drop"] = _ask_list("Linux capabilities to drop", d.get("cap_drop", []))
