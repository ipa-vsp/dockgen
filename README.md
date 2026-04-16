# dockgen — Docker Generator

An interactive wizard that generates Docker Compose and VS Code devcontainer
configurations for ROS and general development environments.

All answers are persisted in `.dockgen.json` so that `dockgen config` can re-run with
your previous choices as defaults, and `dockgen add` can patch a single field
without touching the rest.

---

## Features

- Step-by-step wizard: ROS distro, base image, GPU, display, network, volumes, startup
- **ROS-aware defaults** — `network: host`, `ipc: host`, `ROS_LOCALHOST_ONLY=0`, auto-sourced `setup.bash`
- **GPU detection** — probes `nvidia-smi` / `rocm-smi` and pre-fills the choice
- **Display detection** — reads `WAYLAND_DISPLAY` / `DISPLAY` from the environment
- **VSCode extension scanner** — reads `~/.vscode/extensions` and presents a checklist
- **Custom Dockerfile** — creates a non-root user matching your host UID/GID, installs dev tools
- Outputs: `docker/compose.yml`, `docker/Dockerfile`, `.devcontainer/devcontainer.json`
- Surgical `dockgen add gpu|display|volume` — patch one thing, regenerate everything

---

## Requirements

- Python 3.8+
- Docker (for `dockgen validate` dry-run; not required for file generation)

---

## Installation

```bash
sudo apt-add-repository ppa:prachanda/dockgen
sudo apt update
sudo apt install python3-dockgen
#or
wget "https://launchpad.net/~prachanda/+archive/ubuntu/dockgen/+build/32773446/+files/buildlog_ubuntu-noble-amd64.dockgen_0.1.0_BUILDING.txt.gz"
zcat buildlog_ubuntu-noble-amd64.dockgen_0.1.0_BUILDING.txt.gz | tail -100
``` 

### Option A — pipx (recommended on Ubuntu 22.04 / 24.04)

```bash
sudo apt install pipx          # if not already installed
pipx ensurepath

git clone <repo-url> ~/dockgen
cd ~/dockgen
bash install.sh                # detects pipx automatically
```

### Option B — pip user install

```bash
git clone <repo-url> ~/dockgen
cd ~/dockgen
pip install --user .
```

On Ubuntu 22.04+ you may see a PEP 668 "externally-managed-environment" error.
`install.sh` handles this automatically; if installing manually:

```bash
pip install --user --break-system-packages .
```

### Option C — system-wide (requires sudo)

```bash
cd ~/dockgen
sudo bash install.sh --system
```

### Option D — editable / dev mode (source stays linked)

```bash
cd ~/dockgen
bash install.sh --editable
# or manually:
pip install --user --break-system-packages -e .
```

### After installation

`install.sh` also installs:

| File | Destination |
|------|-------------|
| Bash completion | `~/.local/share/bash-completion/completions/dockgen` |
| Man page | `~/.local/share/man/man1/dockgen.1.gz` |

If `~/.local/bin` is not in your `PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Enable tab completion in the current shell:

```bash
source ~/.local/share/bash-completion/completions/dockgen
```

Or add it to `~/.bashrc` to load automatically on every login.

---

## Quick start

```bash
cd ~/ros_ws/my_project
dockgen new
```

The wizard walks through nine steps:

| Step | What it asks |
|------|-------------|
| 1 | Output format: `compose`, `devcontainer`, or `both` |
| 2 | ROS distro (`jazzy`, `humble`, `iron`, `noetic`, `rolling`, `none`) |
| 3 | Base image (pre-filled from OSRF for ROS) |
| 3b | Custom Dockerfile? (user creation, apt/pip packages) |
| 4a | GPU runtime (auto-probed) |
| 4b | GUI forwarding (auto-probed from environment) |
| 4c | Network mode (`host`, `bridge`, `custom`) |
| 5 | UID/GID passthrough, timezone, extra env vars |
| 6 | Workspace mount + additional bind mounts |
| 7 | Startup command |
| 8 | Devcontainer extras (postCreateCommand, VSCode extensions) |
| 9 | Advanced options (privileged, ipc, cap_add/drop) |

Generated files:

```
my_project/
├── .dockgen.json                   # source of truth — edit and run dockgen config to regenerate
├── docker/
│   ├── compose.yml
│   ├── .env                    # UID/GID for compose variable interpolation
│   └── Dockerfile              # only when custom Dockerfile was chosen
└── .devcontainer/
    ├── devcontainer.json
    └── Dockerfile              # only when custom Dockerfile was chosen
```

---

## Usage

```
dockgen [-w WORKSPACE] COMMAND [args]
```

| Command | Description |
|---------|-------------|
| `dockgen new` | Full wizard from scratch |
| `dockgen new --force` | Overwrite an existing `.dockgen.json` |
| `dockgen config` | Re-run wizard with previous answers as defaults |
| `dockgen add gpu` | Probe GPU and patch config |
| `dockgen add display` | Probe display and patch config |
| `dockgen add volume HOST:CONTAINER` | Append a bind mount |
| `dockgen validate` | Check files exist and run `docker compose config` |
| `dockgen info` | Print current `.dockgen.json` as formatted JSON |

The `-w / --workspace` flag sets the target directory (default: current directory).

### Examples

**ROS 2 Humble with Wayland and NVIDIA GPU:**

```bash
dockgen new
# step 2: humble
# step 4a: nvidia
# step 4b: wayland   (or press Enter — auto-detected if WAYLAND_DISPLAY is set)
# step 4c: host      (default for ROS)
```

**Add GPU to an existing config without re-running the full wizard:**

```bash
dockgen add gpu
```

**Mount a dataset directory:**

```bash
dockgen add volume /datasets:/datasets:ro
```

**Launch the container:**

```bash
cd docker/
docker compose up -d
docker compose exec <service> bash
```

**Open in VS Code devcontainer:**

Open the workspace folder in VS Code and choose
*Reopen in Container* when prompted.

---

## Reconfiguring

Edit answers and regenerate all output files:

```bash
dockgen config
```

All output files are always regenerated from `.dockgen.json` — never edit
`compose.yml` or `devcontainer.json` directly, as your changes will be
overwritten on the next `dockgen config` run.

---

## Uninstallation

### If installed via pipx

```bash
pipx uninstall dockgen
```

### If installed via pip

```bash
pip uninstall dockgen
# or, on externally-managed distros:
pip uninstall --break-system-packages dockgen
```

### Remove completion and man page

```bash
rm -f ~/.local/share/bash-completion/completions/dockgen
rm -f ~/.local/share/man/man1/dockgen.1 ~/.local/share/man/man1/dockgen.1.gz
```

### System-wide uninstall

```bash
sudo pip uninstall dockgen
sudo rm -f /etc/bash_completion.d/dockgen
sudo rm -f /usr/local/share/man/man1/dockgen.1 /usr/local/share/man/man1/dockgen.1.gz
```

### Remove generated files from a project

```bash
rm -f .dockgen.json
rm -rf docker/ .devcontainer/
```
