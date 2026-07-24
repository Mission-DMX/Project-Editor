#version 410 core

// Beam shader (Pass 2: volumetric cone with ray-marched shadows)

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 LocalPos;
out vec3 WorldPos;

void main() {
    LocalPos = aPos;
    vec4 wp = model * vec4(aPos, 1.0);
    WorldPos = wp.xyz;
    gl_Position = projection * view * wp;
}