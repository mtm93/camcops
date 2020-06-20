# server/docker/camcops_server.Dockerfile
#
# Directory structure in container:
#
#   /camcops            All CamCOPS code/binaries.
#       /cfg            Config files are mounted here.
#       /src            Source code for CamCOPS server.
#       /venv           Python 3 virtual environment.
#           /bin        Main "camcops_server" executable lives here.

# -----------------------------------------------------------------------------
# FROM: Base image
# -----------------------------------------------------------------------------
# - Avoid Alpine Linux?
#   https://pythonspeed.com/articles/base-image-python-docker-images/
# - python:3.6-slim-buster? This is a Debian distribution ("buster" is Debian
#   10). Seems to work fine.
# - ubuntu:18.04? Requires "apt install python3" or similar? Quite tricky.
#   Also larger.

FROM python:3.6-slim-buster

# -----------------------------------------------------------------------------
# ADD: files to copy
# -----------------------------------------------------------------------------
# - Syntax: ADD <host_file_spec> <container_dest_dir>
# - The host file spec is relative to the context (and can't go "above" it).
# - This docker file lives in the "server/docker/" directory within the CamCOPS
#   source, so we expect Docker to be told (externally -- see e.g. the Docker
#   Compose file) that the context is our parent directory, "server/". This
#   is the directory containing "setup.py" and therefore the installation
#   directory for our Python package.

ADD . /camcops/src

# -----------------------------------------------------------------------------
# WORKDIR: Set working directory on container.
# -----------------------------------------------------------------------------
# Shouldn't really be necessary.

WORKDIR /camcops

# -----------------------------------------------------------------------------
# RUN: run a command.
# -----------------------------------------------------------------------------
# - A venv is not necessarily required. Our "system" Python only exists to run
#   CamCOPS -- though other things may be installed by the OS.
#   However, we'll use one; it improves predictability.
#
# - Watch out for apt-get:
#
#   - https://stackoverflow.com/questions/27273412/cannot-install-packages-inside-docker-ubuntu-image
#   - https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#run

# Install packages for the operating system.
# - git: because we are currently using a git-based development package via
#   setup.py
# - gcc: required by some Python packages (e.g. psutil)
# - libmagickwand-dev: ImageMagick
# - libmysqlclient-dev: for MySQL access (needed by Python mysqlclient package)
#   ... replaced by libmariadbclient-dev in Debian 10
# - python3-dev: probably installed automatically, but required
# - python3-tk: Tkinter, not installed by default

RUN apt-get update && apt-get install -y \
        gcc \
        git \
        libmagickwand-dev \
        libmariadbclient-dev \
        python3-dev \
        python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Use system python3 to create Python virtual environment (venv).

RUN python3 -m venv /camcops/venv

# Upgrade pip within virtual environment.

RUN /camcops/venv/bin/python3 -m pip install --upgrade pip

# Install CamCOPS in virtual environment.

RUN /camcops/venv/bin/python3 -m pip install /camcops/src

# Install MySQL drivers for Python. Use a C-based one for speed.

RUN /camcops/venv/bin/python3 -m pip install mysqlclient==1.4.6
# ... version 1.3.13 fails to install with: "OSError: mysql_config not found"
# ... version 1.4.6 works fine

# *** upgrade database structure

# -----------------------------------------------------------------------------
# EXPOSE: expose a port.
# -----------------------------------------------------------------------------

EXPOSE 8000

# -----------------------------------------------------------------------------
# CMD: run the foreground task whose lifetime determines the container
# lifetime.
# -----------------------------------------------------------------------------
# Note: can be (and is) overridden by the "command" option in a docker-compose
# file.

# CMD ["/camcops/venv/bin/camcops_server" , "serve_gunicorn"]
CMD ["/bin/bash"]
