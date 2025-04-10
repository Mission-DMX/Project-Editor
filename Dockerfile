FROM ubuntu:latest

# Installiere System-Dependencies
RUN apt update && apt install -y \
    libxcb-xinerama0 libxcb-keysyms1 libxcb-icccm4 ibxcb-shape0 libxcb-render-util0 libxcb-cursor0 \
    libxcb-xkb1 libxkbcommon-x11-0 libxcb-image0

#    libsdl2-dev libsdl2-image-2.0-0 libxcb-keysyms1 libxcb1 libxcb-icccm4 libxcb-image0 libxkbcommon-x11-0 \
#    libxcb-cursor0 libgdk-pixbuf2.0-0 libxcb-shm0 libxcb-xfixes0 libxcb-shape0 libxcb-render-util0  libgtk-3-0 \
#    libcairo2 libatk1.0-0 libxrender1 libxi6 libsm6 libxext6 libgl1-mesa-glx \
#    build-essential wget git\
#    && apt clean

#RUN mkdir /glibc && \
#    cd /glibc && \
#    wget http://ftp.gnu.org/gnu/libc/glibc-2.38.tar.gz && \
#    tar -xvzf glibc-2.38.tar.gz && \
#    mkdir build && cd build && \
#    ../glibc-2.38/configure --prefix=/opt/glibc-2.38 && \
#    make -j$(nproc) && make install

#ENV LD_LIBRARY_PATH=/opt/glibc-2.38/lib:$LD_LIBRARY_PATH



# Installiere Python-Tools
#RUN pip install pdm

WORKDIR /app