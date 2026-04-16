ROS_BASE_IMAGES = {
    "jazzy": "osrf/ros:jazzy-desktop",
    "humble": "osrf/ros:humble-desktop",
    "iron": "osrf/ros:iron-desktop",
    "noetic": "osrf/ros:noetic-desktop-full",
    "rolling": "osrf/ros:rolling-desktop",
}

DISTROS = {
    "jazzy": {"ubuntu": "24.04", "ros_version": 2},
    "humble": {"ubuntu": "22.04", "ros_version": 2},
    "iron": {"ubuntu": "22.04", "ros_version": 2},
    "noetic": {"ubuntu": "20.04", "ros_version": 1},
    "rolling": {"ubuntu": "24.04", "ros_version": 2},
}

COMMON_DEV_APT = [
    "build-essential",
    "ca-certificates",
    "curl",
    "git",
    "sudo",
    "tmux",
    "vim",
    "wget",
]

ROS_DEV_APT = {
    "jazzy": [
        "ros-dev-tools",
        "python3-colcon-common-extensions",
        "python3-rosdep",
    ],
    "humble": [
        "ros-dev-tools",
        "python3-colcon-common-extensions",
        "python3-rosdep",
    ],
    "iron": [
        "ros-dev-tools",
        "python3-colcon-common-extensions",
        "python3-rosdep",
    ],
    "noetic": [
        "python3-rosdep",
        "python3-catkin-tools",
    ],
    "rolling": [
        "ros-dev-tools",
        "python3-colcon-common-extensions",
        "python3-rosdep",
    ],
}


def apt_packages_for(distro, user_extras=None):
    pkgs = list(COMMON_DEV_APT)
    if distro and distro != "none":
        pkgs.extend(ROS_DEV_APT.get(distro, []))
    if user_extras:
        pkgs.extend(user_extras)
    seen = set()
    out = []
    for p in pkgs:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out
