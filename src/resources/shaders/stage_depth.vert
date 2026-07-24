#version 410 core

// Depth-only shader (Pass 0: shadow map generation)

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;  // unused but matches VAO layout
uniform mat4 lightSpaceMatrix;
uniform mat4 model;
void main() {
    gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0);
}