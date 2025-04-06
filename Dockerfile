FROM python:3.13-slim

# Installiere System-Dependencies
RUN apt update && apt install -y \
    libxcb-keysyms1 libxcb1 libxcb-icccm4 libxcb-image0 \
    libxcb-shm0 libxcb-xfixes0 libxcb-shape0 libxcb-render-util0 \
    libxrender1 libxi6 libsm6 libxext6 libgl1-mesa-glx \
    build-essential cmake \
    && apt clean

RUN groupadd -r runner && useradd -r -g runner -m runner

RUN mkdir -p /github/home/.cache/pip && \
    chown -R runner:runner /github/home/.cache/pip && \
    chmod -R 775 /github/home/.cache/pip

USER runner

# Installiere Python-Tools
RUN pip install --upgrade pip && pip install pyinstaller

WORKDIR /app