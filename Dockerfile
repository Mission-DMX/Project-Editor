FROM ubuntu:latest

# Installiere System-Dependencies
RUN apt update && apt install -y \
    binutils \
    libxcb-xinerama0 libxcb-keysyms1 libxcb-icccm4 libxcb-shape0 libxcb-render-util0 libxcb-cursor0 \
    libxcb-xkb1 libxkbcommon-x11-0 libxcb-image0\
    git\
    && apt clean

#    libsdl2-dev libsdl2-image-2.0-0 libxcb-keysyms1 libxcb1 libxcb-icccm4 libxcb-image0 libxkbcommon-x11-0 \
#    libxcb-cursor0 libgdk-pixbuf2.0-0 libxcb-shm0 libxcb-xfixes0 libxcb-shape0 libxcb-render-util0  libgtk-3-0 \
#    libcairo2 libatk1.0-0 libxrender1 libxi6 libsm6 libxext6 libgl1-mesa-glx \
#    build-essential wget git\
#    && apt clean



# Installiere Python-Tools
#RUN pip install pdm

WORKDIR /app