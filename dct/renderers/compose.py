import os
from pathlib import Path

from dct.renderers import dockerfile as df


def render(answers, workspace):
    out_dir = Path(workspace) / "docker"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    compose_path = out_dir / "compose.yml"
    compose_path.write_text(_compose(answers))
    written.append(compose_path)

    env_text = _envfile(answers)
    if env_text:
        env_path = out_dir / ".env"
        env_path.write_text(env_text)
        written.append(env_path)

    if answers.get("dockerfile") == "custom":
        written.append(df.render(answers, out_dir))

    return written


def _compose(a):
    svc = a["service_name"]
    L = []
    L.append("services:")
    L.append(f"  {svc}:")
    if a.get("dockerfile") == "custom":
        L.append("    build:")
        L.append("      context: .")
        L.append("      dockerfile: Dockerfile")
        L.append("      args:")
        L.append(f"        USERNAME: {a.get('dev_user') or 'dev'}")
        L.append('        USER_UID: "${UID}"')
        L.append('        USER_GID: "${GID}"')
    else:
        L.append(f"    image: {a['base_image']}")
    L.append(f"    container_name: {svc}")
    L.append("    stdin_open: true")
    L.append("    tty: true")

    if a.get("gpu") == "nvidia":
        L.append("    runtime: nvidia")

    if a.get("network") == "host":
        L.append("    network_mode: host")
    elif a.get("network") == "custom":
        L.append("    networks:")
        L.append(f"      - {a.get('network_name') or 'dct_net'}")

    if a.get("ipc_host"):
        L.append("    ipc: host")

    if a.get("privileged"):
        L.append("    privileged: true")

    if a.get("passthrough_uid"):
        L.append('    user: "${UID}:${GID}"')

    caps_add = a.get("cap_add") or []
    if caps_add:
        L.append("    cap_add:")
        for c in caps_add:
            L.append(f"      - {c}")

    caps_drop = a.get("cap_drop") or []
    if caps_drop:
        L.append("    cap_drop:")
        for c in caps_drop:
            L.append(f"      - {c}")

    envs = _compose_env(a)
    if envs:
        L.append("    environment:")
        for k, v in envs.items():
            L.append(f'      {k}: "{v}"')

    vols = _compose_volumes(a)
    if vols:
        L.append("    volumes:")
        for v in vols:
            L.append(f"      - {v}")

    devs = _compose_devices(a)
    if devs:
        L.append("    devices:")
        for dev in devs:
            L.append(f"      - {dev}")

    if a.get("startup"):
        L.append(f"    command: {a['startup']}")

    if a.get("network") == "custom":
        L.append("")
        L.append("networks:")
        L.append(f"  {a.get('network_name') or 'dct_net'}:")
        L.append("    driver: bridge")

    return "\n".join(L) + "\n"


def _compose_env(a):
    env = dict(a.get("env") or {})
    if a.get("timezone"):
        env.setdefault("TZ", a["timezone"])
    if a.get("display") == "x11":
        env.setdefault("DISPLAY", "${DISPLAY}")
        env.setdefault("QT_X11_NO_MITSHM", "1")
    elif a.get("display") == "wayland":
        env.setdefault("WAYLAND_DISPLAY", "${WAYLAND_DISPLAY}")
        env.setdefault("XDG_RUNTIME_DIR", "${XDG_RUNTIME_DIR}")
        env.setdefault("QT_QPA_PLATFORM", "wayland")
    if a.get("gpu") == "nvidia":
        env.setdefault("NVIDIA_VISIBLE_DEVICES", "all")
        env.setdefault("NVIDIA_DRIVER_CAPABILITIES", "all")
    if a.get("ros_distro") and a.get("ros_distro") != "none" and a.get("network") == "host":
        env.setdefault("ROS_LOCALHOST_ONLY", "0")
    return env


def _compose_volumes(a):
    vols = []
    if a.get("workspace_mount"):
        vols.append(f"{os.getcwd()}:/workspace")
    if a.get("display") == "x11":
        vols.append("/tmp/.X11-unix:/tmp/.X11-unix:rw")
    elif a.get("display") == "wayland":
        vols.append("${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}")
    vols.extend(a.get("extra_mounts") or [])
    return vols


def _compose_devices(a):
    devs = []
    if a.get("gpu") == "amd":
        devs.append("/dev/dri:/dev/dri")
        devs.append("/dev/kfd:/dev/kfd")
    if a.get("display") == "wayland":
        devs.append("/dev/dri:/dev/dri")
    return devs


def _envfile(a):
    if not a.get("passthrough_uid"):
        return ""
    try:
        uid = os.getuid()
        gid = os.getgid()
    except AttributeError:
        return ""
    return f"UID={uid}\nGID={gid}\n"
