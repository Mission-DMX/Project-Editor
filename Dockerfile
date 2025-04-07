FROM python:3.13-slim

# Installiere System-Dependencies
RUN apt update && apt install -y \
    libsdl2-dev libxcb-keysyms1 libxcb1 libxcb-icccm4 libxcb-image0 libxkbcommon-x11-0 libxcb-cursor0  \
    libgdk-pixbuf2.0-0 libxcb-shm0 libxcb-xfixes0 libxcb-shape0 libxcb-render-util0  libgtk-3-0 libcairo2 libatk1.0-0\
    libxrender1 libxi6 libsm6 libxext6 libgl1-mesa-glx \
    build-essential git\
    && apt clean


# Installiere Python-Tools
COPY requirements.txt .
RUN pip install --upgrade pip && pip install pyinstaller && pip install -r requirements.txt

WORKDIR /app