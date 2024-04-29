"""
NOM : DEFOING
PRÉNOM : Daniel
SECTION : INFO
MATRICULE : 000589910
"""

# DOCUMENTATION : Chapter II.a


class Pixel():
    def __init__(self, r: int, g: int, b: int):
        self._colors = (r, g, b)
        if not all(isinstance(val, int) for val in self.colors):
            raise TypeError("Pixel color value not set to an integer.")
        if not all(0 <= val <= 255 for val in self.colors):
            possible_faults = {'r': r, 'g': g, 'b': b}
            actual_faults = {channel: value for channel, value in possible_faults.items()
                              if not 0 <= value <= 255}
            raise ValueError("Invalid pixel color value (0-255) for the following :"
                             f"{actual_faults}")

    @property
    def colors(self) -> tuple[int, int, int]:
        return self._colors

    def __eq__(self, other) -> bool:
        return isinstance(other, Pixel) and self.colors == other.colors

    def __hash__(self):
        return hash((self.colors))
