from model.filter import Filter, VirtualFilter


def construct_virtual_filter_instance(f: Filter) -> VirtualFilter:
    if not f.is_virtual_filter:
        raise ValueError("The provided filter is not a virtual description.")
    match f.filter_type:
        case -1:
            # TODO return virtual filter that instantiates a preset (as described in issue #48)
            pass
        case -2:
            # TODO implement pan/tilt position constant (that can be configured using the joystick as well as a
            #  two dimensional state diagram
            pass
        case -3:
            # TODO implement virtual filter for cues (in order to provide preview based editing)
            pass
        case -4:
            # TODO implement effects stack virtual filter (as described in issue #87)
            pass
        case -5:
            # TODO implement virtual filter for auto tracker
            pass
    pass
