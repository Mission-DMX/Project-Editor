from model import Universe
import proto.UniverseControl_pb2

issued_test_universes = 0

class TestUniverse(Universe):
    """Test Universe mockup"""

    def __init__(self):
        global issued_test_universes
        definition = proto.UniverseControl_pb2.Universe(id=issued_test_universes)
        #definition.name = "Test Universe"
        issued_test_universes += 1
        super().__init__(definition)
