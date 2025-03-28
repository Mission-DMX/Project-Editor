#version 410 core

in vec2 position;
in vec2 texture_coordinate;

uniform vec2 in_cursor_position;
uniform vec2 in_cord_size;

uniform mat4 projectionMatrix;
uniform mat4 modelMatrix;

smooth out vec2 ioVertexTexCoord;
smooth out vec2 cursor_position;
smooth out vec2 cord_size;

void main() {
    mat4 mvpMatrix = projectionMatrix * modelMatrix;
    gl_Position = mvpMatrix * vec4(position, 0.0, 1.0);
    ioVertexTexCoord = texture_coordinate;
    cursor_position = in_cursor_position;
    cord_size = in_cord_size;
}