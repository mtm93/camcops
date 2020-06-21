# server/docker/camcops.Dockerfile
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
#
# - There is also something good about minimizing the number of RUN commands:
#
#   - https://docs.docker.com/engine/reference/builder/#run
#   - https://stackoverflow.com/questions/39223249/multiple-run-vs-single-chained-run-in-dockerfile-what-is-better

# Install packages for the operating system.
#
# - gcc: required by some Python packages (e.g. psutil)
# - gdebi: allows us to auto-install dependencies when installing .deb files
#   quasi-manually
# - git: because we are currently using a git-based development package via
#   setup.py
# - libmagickwand-dev: ImageMagick, used by CamCOPS
# - libmysqlclient-dev: for MySQL access (needed by Python mysqlclient package)
#   ... replaced by libmariadbclient-dev in Debian 10
# - python3-dev: probably installed automatically, but required
# - python3-tk: Tkinter for Python, not installed by default
# - wget: for fetching other stuff! See below.
#
# Also, install wkhtmltopdf in a different way, as above.
#
# - wkhtmltopdf is required by CamCOPS for PDF generation. However, the Debian
#   version (0.12.5) is NOT the "patched Qt" edition, so we have to do that
#   more "manually". See
#   - https://wkhtmltopdf.org/downloads.html
#   - https://stackoverflow.com/questions/38262173/how-to-correctly-install-wkhtmltopdf-on-debian-64-bit

RUN echo "- Updateing package information..." \
    && apt-get update \
    && echo "- Installing operating system packages..." \
    && apt-get install -y \
        gcc \
        gdebi \
        git \
        libmagickwand-dev \
        libmariadbclient-dev \
        python3-dev \
        python3-tk \
        wget \
    && echo "- Fetching wkhtmltopdf with patched Qt..." \
    && wget -O /tmp/wkhtmltopdf.deb \
        https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb \
    && echo "- Installing wkhtmltopdf..." \
    && gdebi --non-interactive /tmp/wkhtmltopdf.deb \
    && echo "- Cleaning up..." \
    && rm /tmp/wkhtmltopdf.deb \
    && rm -rf /var/lib/apt/lists/*

# - Make /var/lock/camcops
# - Make /var/tmp/camcops
# - Use system python3 to create Python virtual environment (venv).
# - Upgrade pip within virtual environment.
# - Install CamCOPS in virtual environment.
# - Install MySQL drivers for Python. Use a C-based one for speed.
#   - use mysqlclient
#   - version 1.3.13 fails to install with: "OSError: mysql_config not found"
#   - version 1.4.6 works fine

RUN echo "- Making directories..." \
    && mkdir -p /var/lock/camcops \
    && mkdir -p /var/tmp/camcops \
    && echo "- Creating Python 3 virtual environment..." \
    && python3 -m venv /camcops/venv \
    && echo "- Upgrading pip within virtual environment..." \
    && /camcops/venv/bin/python3 -m pip install --upgrade pip \
    && echo "- Installing CamCOPS and Python database drivers..." \
    && /camcops/venv/bin/python3 -m pip install \
        /camcops/src \
        mysqlclient==1.4.6


# -----------------------------------------------------------------------------
# EXPOSE: expose a port.
# -----------------------------------------------------------------------------
# We'll do this via docker-compose instead.

# EXPOSE 8000

# -----------------------------------------------------------------------------
# CMD: run the foreground task whose lifetime determines the container
# lifetime.
# -----------------------------------------------------------------------------
# Note: can be (and is) overridden by the "command" option in a docker-compose
# file.

# CMD ["/camcops/venv/bin/camcops_server" , "serve_gunicorn"]
# CMD ["/bin/bash"]
