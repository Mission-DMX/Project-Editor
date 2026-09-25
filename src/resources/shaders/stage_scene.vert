#version 410 core

// Scene shader (Pass 1: Phong + spotlights + PCF shadows)

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 FragPos;
out vec3 Normal;

void main() {
    vec4 wp = model * vec4(aPos, 1.0);
    FragPos = wp.xyz;
    Normal = mat3(transpose(inverse(model))) * aNormal;
    gl_Position = projection * view * wp;
}