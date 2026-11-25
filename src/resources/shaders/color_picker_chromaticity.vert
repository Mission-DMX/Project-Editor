#version 410 core

layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aXY;

out vec2 vXY;

void main() {
    vXY = aXY;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
