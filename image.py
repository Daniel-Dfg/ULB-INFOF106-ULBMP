"""
NOM : DEFOING
PRÉNOM : Daniel
SECTION : INFO
MATRICULE : 000589910
"""

# DOCUMENTATION : Chapter II.b


from pixel import Pixel


class Image():
    def __init__(self, width: int, height: int, pixels: list[Pixel]):
        self._width, self._height, self._pix_list = width, height, pixels
        if self.width * self.height != len(self.pix_list) or (self.width < 0 and self.height < 0):
            raise ValueError("Amount of defined pixels inconsistent with the given image size."
                             f"Expected {self.width} x {self.height} = {self.width*self.height},"
                             f"got {len(self.pix_list)}.")
        if not all(isinstance(elem, Pixel) for elem in self.pix_list):
            raise TypeError("At least one element in the given list of pixels cannot be recognized as such.")

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def ImgDimensions(self) -> tuple[int, int]:
        return self.width, self.height

    @property
    def pix_list(self) -> list[Pixel]:
        return self._pix_list

    @property
    def color_count(self) -> int:
        # could've been defined within the __init__ method, but it's only
        # used once in encoding.py anyway
        return len(set(self.pix_list))

    @property
    def unique_colors(self) -> list:
        # Same idea as above, no need to initialize it on Image creation if I
        # don't necessarily need it
        return list(set(self.pix_list))

    def __getitem__(self, position: tuple[int, int]) -> Pixel:
        absolute_pos = self.get_pos_in_pix_list(position)
        return self.pix_list[absolute_pos]

    def __setitem__(self, position: tuple[int, int], new_pixel: Pixel) -> None:
        absolute_pos = self.get_pos_in_pix_list(position)
        self.pix_list[absolute_pos] = new_pixel

    def __eq__(self, other) -> bool:
        return self.ImgDimensions == other.ImgDimensions and self.pix_list == other.pix_list

    def get_pos_in_pix_list(self, pos: tuple[int, int]) -> bool:
        if any(not isinstance(coord, int) for coord in pos):
            raise TypeError("Invalid position parameter.")

        if not (0 <= pos[0] < self.width and 0 <= pos[1] < self.height): # if x or y coordinate out of bounds
            raise IndexError("Invalid selected position. Image size was :"
                             f"{self.ImgDimensions[0]} x {self.ImgDimensions[1]}. Chosen pos  : {pos}.")

        return pos[0] + pos[1]*self.width  # represents the index in pix_list
