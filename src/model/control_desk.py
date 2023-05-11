import proto.Console_pb2


class BankSet():
    def __init__(self, bank_id: str):
        self.id = bank_id
        self.pushed_to_fish = False

    def update(self):
        if self.pushed_to_fish:
            pass