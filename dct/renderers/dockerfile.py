from pathlib import Path

from dct import ros


def render(answers, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "Dockerfile"
    path.write_text(_build(answers))
    return path


def _build(a):
    distro = a.get("ros_distro")
    has_ros = bool(distro) and distro != "none"
    user = a.get("dev_user") or "dev"

    L = []
    L.append(f"FROM {a['base_image']}")
    L.append("")
    L.append(f"ARG USERNAME={user}")
    L.append("ARG USER_UID=1000")
    L.append("ARG USER_GID=1000")
    L.append("")
    L.append("ENV DEBIAN_FRONTEND=noninteractive")
    L.append("")
    L.append("RUN set -eux; \\")
    L.append("    if getent passwd $USER_UID >/dev/null; then \\")
    L.append("        userdel -r \"$(getent passwd $USER_UID | cut -d: -f1)\"; \\")
    L.append("    fi; \\")
    L.append("    if getent group $USER_GID >/dev/null; then \\")
    L.append("        groupdel \"$(getent group $USER_GID | cut -d: -f1)\"; \\")
    L.append("    fi; \\")
    L.append("    groupadd --gid $USER_GID $USERNAME; \\")
    L.append("    useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME; \\")
    L.append("    apt-get update; \\")
    L.append("    apt-get install -y --no-install-recommends sudo; \\")
    L.append("    echo \"$USERNAME ALL=(root) NOPASSWD:ALL\" > /etc/sudoers.d/$USERNAME; \\")
    L.append("    chmod 0440 /etc/sudoers.d/$USERNAME; \\")
    L.append("    rm -rf /var/lib/apt/lists/*")
    L.append("")

    apt = ros.apt_packages_for(distro, a.get("apt_packages"))
    if apt:
        L.append("RUN apt-get update \\")
        L.append("    && apt-get install -y --no-install-recommends \\")
        for i, pkg in enumerate(apt):
            suffix = " \\" if i < len(apt) - 1 else " \\"
            L.append(f"        {pkg}{suffix}")
        L.append("    && rm -rf /var/lib/apt/lists/*")
        L.append("")

    pip = a.get("pip_packages") or []
    if pip:
        L.append("RUN pip3 install --no-cache-dir \\")
        for i, pkg in enumerate(pip):
            suffix = " \\" if i < len(pip) - 1 else ""
            L.append(f"        {pkg}{suffix}")
        L.append("")

    if has_ros:
        L.append(f"RUN echo 'source /opt/ros/{distro}/setup.bash' >> /home/$USERNAME/.bashrc \\")
        L.append("    && echo '[ -f /workspace/install/setup.bash ] && source /workspace/install/setup.bash' >> /home/$USERNAME/.bashrc")
        L.append("")

    L.append("USER $USERNAME")
    L.append("WORKDIR /workspace")
    return "\n".join(L) + "\n"
