#version 410 core

smooth in vec2 ioVertexTexCoord;
smooth in vec2 cursor_position;
smooth in vec2 cord_size;

layout(location = 0) out vec4 out_color;

bool is_visible(vec2 position) {
    // TODO
    return mod(position.x, 2) == 0;
}

bool is_cursor_overlap(vec2 position, vec2 cp) {
    // TODO
    return false;
}

vec4 calculate_position_color(vec2 position) {
    // TODO calcluate color based on coordinate
    return vec4(1.0, 0.0, 0.0, 1.0);
}

void main() {
    vec2 pos = gl_FragCoord.ab - ioVertexTexCoord;
    if(!is_visible(pos)) {
        discard;
    }
    /*if (is_cursor_overlap(pos, cursor_position)) {
        out_color = vec4(1.0, 1.0, 1.0, 1.0);
    } else {
        out_color = calculate_position_color(pos);
    }*/
    out_color = vec4(gl_FragCoord.xy / cord_size.xy, 0.0, 1.0);
    //gl_FragColor = out_color;
}