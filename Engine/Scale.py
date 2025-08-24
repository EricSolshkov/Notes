from .Note import Note


class Scale:
    """
    Scale is a series of notes, formed as a sequence of intervals.
    """

    def __init__(self, name: str, notes: list[Note] = None):
        self.notes = []
        self.name = name
        for n in notes:
            self.notes.append(n)

    def __repr__(self):
        return f"Scale({self.name}, {self.notes})"
