FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-xfixes0 \
    libdbus-1-3 \
    libfontconfig1 \
    libxkbcommon-x11-0 \
    libegl1 \
    libsm6 \
    libice6 \
    dbus \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY README.md .
COPY trackora trackora/

RUN pip install --no-cache-dir -e .

ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1

CMD ["trackora-gui"]
