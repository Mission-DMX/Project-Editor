#version 410 core

in vec2 position;
in vec2 texture_coordinate;

uniform struct {
	mat4 projectionMatrix;
	mat4 modelMatrix;
} projection_matrices;

smooth out vec2 ioVertexTexCoord;

void main() {
    mat4 mvpMatrix = projection_matrices.projectionMatrix * projection_matrices.modelMatrix;
    gl_Position = mvpMatrix * vec4(position, 0.0, 1.0);
    ioVertexTexCoord = texture_coordinate;
}