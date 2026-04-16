import json
from pathlib import Path

from dockgen.renderers import dockerfile as df


def render(answers, workspace):
    out_dir = Path(workspace) / ".devcontainer"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    cfg = _build(answers)
    path = out_dir / "devcontainer.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    written.append(path)

    if answers.get("dockerfile") == "custom":
        written.append(df.render(answers, out_dir))

    return written


def _build(a):
    cfg = {"name": a["service_name"]}

    if a.get("dockerfile") == "custom":
        cfg["build"] = {
            "dockerfile": "Dockerfile",
            "context": ".",
            "args": {
                "USERNAME": a.get("dev_user") or "dev",
            },
        }
    else:
        cfg["image"] = a["base_image"]

    run_args = []
    if a.get("network") == "host":
        run_args.append("--network=host")
    if a.get("ipc_host"):
        run_args.append("--ipc=host")
    if a.get("gpu") == "nvidia":
        run_args.append("--runtime=nvidia")
        run_args.append("--gpus=all")
    elif a.get("gpu") == "amd":
        run_args.extend([
            "--device=/dev/dri",
            "--device=/dev/kfd",
        ])
    if a.get("privileged"):
        run_args.append("--privileged")
    for c in a.get("cap_add") or []:
        run_args.append(f"--cap-add={c}")
    for c in a.get("cap_drop") or []:
        run_args.append(f"--cap-drop={c}")
    if run_args:
        cfg["runArgs"] = run_args

    env = dict(a.get("env") or {})
    if a.get("timezone"):
        env.setdefault("TZ", a["timezone"])
    if a.get("display") == "x11":
        env.setdefault("DISPLAY", "${localEnv:DISPLAY}")
        env.setdefault("QT_X11_NO_MITSHM", "1")
    elif a.get("display") == "wayland":
        env.setdefault("WAYLAND_DISPLAY", "${localEnv:WAYLAND_DISPLAY}")
        env.setdefault("XDG_RUNTIME_DIR", "${localEnv:XDG_RUNTIME_DIR}")
        env.setdefault("QT_QPA_PLATFORM", "wayland")
    if a.get("gpu") == "nvidia":
        env.setdefault("NVIDIA_VISIBLE_DEVICES", "all")
        env.setdefault("NVIDIA_DRIVER_CAPABILITIES", "all")
    if a.get("ros_distro") and a.get("ros_distro") != "none" and a.get("network") == "host":
        env.setdefault("ROS_LOCALHOST_ONLY", "0")
    if env:
        cfg["containerEnv"] = env

    mounts = []
    if a.get("display") == "x11":
        mounts.append("source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind")
    elif a.get("display") == "wayland":
        mounts.append("source=${localEnv:XDG_RUNTIME_DIR},target=${localEnv:XDG_RUNTIME_DIR},type=bind")
    for m in a.get("extra_mounts") or []:
        if ":" in m:
            host, _, container = m.partition(":")
            mounts.append(f"source={host},target={container},type=bind")
    if mounts:
        cfg["mounts"] = mounts

    if a.get("workspace_mount"):
        target = a.get("container_mount") or "/workspace"
        cfg["workspaceMount"] = f"source=${{localWorkspaceFolder}},target={target},type=bind"
        cfg["workspaceFolder"] = target

    if a.get("vscode_extensions"):
        cfg["customizations"] = {
            "vscode": {"extensions": list(a["vscode_extensions"])}
        }

    if a.get("dockerfile") == "custom" and a.get("dev_user"):
        cfg["remoteUser"] = a["dev_user"]
        if a.get("passthrough_uid", True):
            cfg["updateRemoteUserUID"] = True

    if a.get("post_create"):
        cfg["postCreateCommand"] = a["post_create"]

    return cfg
