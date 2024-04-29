"""
NOM : DEFOING
PRÉNOM : Daniel
SECTION : INFO
MATRICULE : 000589910
"""

# README : Chapter II.c


from image import Image
from pixel import Pixel
from convertor import Convertor


ULBMP_BYTES = "ULBMP".encode("ASCII")
LAST_VERSION = 4
HEADER_LENGTH_V1V2 = 12  # ULBMP + VER + 2 bytes for header length, image width and image height
PIXEL_SUBELEMS = 3  # R, G, B
RGB_BIN_SIGNATURES_V4 = {'r': 0b1000, 'g': 0b1001, 'b': 0b1010}  # useful for v4 (see 'save_to' method, Encoder class)


class Encoder():
    def __init__(self, img: Image, version: int = 1, **kwargs):
        self.img_to_encode, self.encoding_version = img, version
        if not ((0 < self.encoding_version <= LAST_VERSION) and isinstance(version, int)):
            raise NotImplementedError(f"Version number incorrect. Last version is {LAST_VERSION}.0")
        if ("rle" not in kwargs or "depth" not in kwargs) and version == 3:
            raise ValueError("Argument(s) missing for version 3 encoding.")
        else:
            if self.encoding_version == 3:
                self._rle, self._pixel_depth = kwargs["rle"], kwargs["depth"]
                if self.pixel_depth not in [1, 2, 4, 8, 24]:
                    raise ValueError(f"Invalid pixel depth ({self.pixel_depth} given).")
                if self.rle and self.pixel_depth < 8:
                    raise NotImplementedError("RLE not supported for bit depths < 8.")

    @property
    def rle(self) -> bool:
        return self._rle

    @property
    def pixel_depth(self) -> int:
        return self._pixel_depth

    @property
    def HeaderLength(self) -> int:
        """
        Dynamic header length calculator (see global constants on top)
        In summary, a header is made of (optional stuff (specific to 3.0 version) between brackets) :
        ULBMP + VER + Header length + width + height + [pixel depth(bpp)] +[rle (0 or 1)] + [color palette]
        """
        length = HEADER_LENGTH_V1V2  # = 12
        if self.encoding_version == 3:
            length += 2  # 1 byte for bpp (= pixel depth), 1 for rle
            if self.pixel_depth != 24:
                length += PIXEL_SUBELEMS * (self.img_to_encode.color_count)  # palette length
        return length

    def save_to(self, path: str) -> None:
        # README : Chapter II.c.1
        # step 1 : collect and write header elements
        with open(path, 'wb') as encoding_file:
            width, height = self.img_to_encode.ImgDimensions
            header_elems = [ULBMP_BYTES, int.to_bytes(self.encoding_version, 1, byteorder='little', signed=False)]
            # Current (known) header at this point : ULBMP + Version + ...
            for main_info in [self.HeaderLength, width, height]:
                header_elems.append(int.to_bytes(main_info, 2, byteorder='little', signed=False))
            # Current (known) header at this point : ULBMP + Version + Header length + width + height + [...]
                
            if self.encoding_version == 3:
                # [pixel depth] and [rle] must be added to the header
                header_elems.extend([int.to_bytes(self.pixel_depth, 1, byteorder='little', signed=False),
                                     int.to_bytes(int(self.rle), 1, byteorder='little', signed=False)])

            # I could've done all of that without using a list, but I wanted to keep things as explicit as
            # possible (since memory cost for such a list is probably negligible anyway)
            for elem in header_elems:
                encoding_file.write(elem)

            if self.encoding_version == 1 or (self.encoding_version == 3 and self.pixel_depth == 24 and not self.rle):
                # Simply writing stuff rgb group of channels per rgb group of channels (not for encoding a palette)
                self.rgb_and_write(encoding_file, is_a_palette=False)

            elif self.encoding_version == 2 or (self.encoding_version == 3 and self.pixel_depth == 24 and self.rle):
                # Canvas : get the amount of occurences of each Pixel, the rgb channels of the Pixel in question,
                # then for each listed 'block' of these 4 elements, just write them all !
                self.streak_and_write(encoding_file, rle_and_bbp8=False)

            elif self.encoding_version == 3 and self.pixel_depth != 24:
                # Same canvas than for v1 (or v3 without palette and rle), but we're considering the fact that
                # we must firstly encode a palette here (see README for an in-depth explanation of this)
                self.rgb_and_write(encoding_file, is_a_palette=True)

                if not self.rle:
                    # i.e: if depth = 4, one pixel is on 4 bits => 2 per byte
                    subelems_per_byte = 8 // self.pixel_depth
                    # 'amount_of_pixels' includes 'fake' pixels (used for pading)
                    amount_of_pixels = width * height
                    for group_i in range(0, amount_of_pixels, subelems_per_byte):
                        converted_pixels = self.img_to_encode.pix_list[group_i: group_i + subelems_per_byte]
                        # see convertor.py file for more details (README : Chapter II.d)
                        encoding_file.write(int.to_bytes(Convertor.byte_maker(converted_pixels, self.pixel_depth,
                                                                              self.img_to_encode.unique_colors),
                                                         length=1, byteorder='little', signed=False))

                elif self.rle and self.pixel_depth == 8:
                    # list all streaks (amount of repetitions, ref to Pixels' palette),
                    # and write them (each ref to the palette being on 1 byte (8 bits))
                    self.streak_and_write(encoding_file, rle_and_bbp8=True)
                else:
                    raise NotImplementedError("RLE not supported for bit depths < 8.")

            elif self.encoding_version == 4:
                """
                IMPORTANT : you may notice 'magical' additions and substractions in the following lines - like
                a '+ 2' popping out of nowhere for each rgb channel for the encoding of a Small Difference 
                (labelled SMALL DIFF). It's just that every value has to be encoded as a positive one in order to 
                make the image Decoding easier. Notice that the load_from method (from the Decoder class)
                "reverts" this process, by applying substractions to the read values.
                I'll call these 'magical' operations "pos_makers" (for 'positive makers').
                But as usual, more on that in the README (Chapter II.c.A) 
                """
                # Step 1 : set up a base Pixel (more info over this encoding method in README, Chapter II.c.1)
                last_pixel = Pixel(0, 0, 0)
                for this_pixel in self.img_to_encode.pix_list:
                    final_val = 0
                    last_r, last_g, last_b = last_pixel.colors
                    r, g, b = this_pixel.colors
                    diff_red, diff_green, diff_blue = r - last_r, g - last_g, b - last_b

                    # Step 2 : find the difference and get the values to write right

                    # SMALL DIFF - Signature 00xxxxxx (1 byte)
                    if (-2 <= diff_red <= 1) and (-2 <= diff_green <= 1) and (-2 <= diff_blue <= 1):
                        rgb_pos_maker = 2
                        diff_red, diff_green, diff_blue = diff_red + rgb_pos_maker, \
                                                          diff_green + rgb_pos_maker, \
                                                          diff_blue + rgb_pos_maker
                        # final byte composition : 00 + diff_red (2) + diff_green (2) + diff_blue (2)
                        final_val = (diff_red << 4) + (diff_green << 2) + diff_blue
                        bytes_used = 1

                    # MEDIUM DIFF - Signature 01xxxxxx xxxxxxxx (2 bytes)
                    elif (-32 <= diff_green <= 31) and (-8 <= diff_red - diff_green <= 7) and (-8 <= diff_blue - diff_green <= 7):
                        rb_pos_makers = 8
                        g_pos_maker = 32
                        delta_rg, delta_bg, diff_green = diff_red - diff_green + rb_pos_makers, \
                                                         diff_blue - diff_green + rb_pos_makers, \
                                                         diff_green + g_pos_maker

                        # final bytes composition : 01 + diff_green (6) + delta (dg, dr) (4) + delta (db, dg) (4)
                        final_val = ((1 << 6) + diff_green << 8) + (delta_rg << 4) + delta_bg
                        bytes_used = 2

                    # BIG DIFF RED - Signature 1000xxxx xxxxxxxx xxxxxxxx (all BIG DIFFS on 3 bytes)
                    elif -128 <= diff_red <= 127 and -32 <= diff_green - diff_red <= 31 and -32 <= diff_blue - diff_red <= 31:
                        final_val = Convertor.big_diff_rgb_maker(
                            {"r": diff_red, "g": diff_green, "b": diff_blue}, ["r", RGB_BIN_SIGNATURES_V4["r"]])
                        bytes_used = 3

                    # BIG DIFF GREEN - Signature 1001xxxx xxxxxxxx xxxxxxxx
                    elif -128 <= diff_green <= 127 and -32 <= diff_red - diff_green <= 31 and -32 <= diff_blue - diff_green <= 31:
                        final_val = Convertor.big_diff_rgb_maker(
                            {"r": diff_red, "g": diff_green, "b": diff_blue}, ["g", RGB_BIN_SIGNATURES_V4["g"]])
                        bytes_used = 3

                    # BIG DIFF BLUE - Signature 1010xxxx xxxxxxxx xxxxxxxx
                    elif -128 <= diff_blue <= 127 and -32 <= diff_red - diff_blue <= 31 and -32 <= diff_green - diff_blue <= 31:
                        final_val = Convertor.big_diff_rgb_maker(
                            {"r": diff_red, "g": diff_green, "b": diff_blue}, ["b", RGB_BIN_SIGNATURES_V4['b']])
                        bytes_used = 3

                    # NEW PIXEL - Signature : 11111111 xxxxxxxx xxxxxxxxx xxxxxxxx (4 bytes)
                    else:
                        shift = 24
                        for elem in [0xff, r, g, b]:  # 0xff = 0b11111111 (signature)
                            final_val += elem << shift
                            shift -= 8
                        bytes_used = 4
                        # final byte composition : 11111111 + r (8) + g (8) + b (8)
                    
                    encoding_file.write(int.to_bytes(final_val, bytes_used, byteorder='big', signed=False))
                    last_pixel = Pixel(r, g, b)

    def streak_and_write(self, encoding_file, rle_and_bbp8: bool):
        """
        Creates a list that references ans writes every "streak of pixels" 
        found in the image to encode (self.img_to_encode).
        This function is multifonctional : if needed, it can adapt
        itself to version 3 encoding by writing content according to
        the image's palette.
        """
        pix_index = 0  # goes through the image's pixel list
        while pix_index < len(self.img_to_encode.pix_list):
            streak_length = 1
            streak_elem = self.img_to_encode.pix_list[pix_index]
            pix_index += 1
            # the last part of the condition is here because streaks are written on 8 bytes.
            while pix_index < len(self.img_to_encode.pix_list) and \
                    self.img_to_encode.pix_list[pix_index] == streak_elem and \
                    streak_length < 255:
                streak_length += 1
                pix_index += 1
            if rle_and_bbp8:
                ref_to_palette = self.img_to_encode.unique_colors.index(streak_elem)
                writing_content = [streak_length, ref_to_palette]
            else:
                writing_content = [streak_length] + [rgb_channel for rgb_channel in streak_elem.colors]
            for subelem in writing_content:
                encoding_file.write(int.to_bytes(subelem, 1, byteorder='big', signed=False))

    def rgb_and_write(self, encoding_file, is_a_palette: bool) -> None:
        """
        Writes rgb channels from a given list of colors. Notice that this function,
        just like streak_and_write, is multifonctional ; since writing a color
        palette is equivalent to writing a bunch of individual rgb channels, why not merge
        these two processes in a single function ?
        """
        if is_a_palette:
            group_elems = self.img_to_encode.unique_colors
        else:
            group_elems = self.img_to_encode.pix_list
        for each_pix in group_elems:
            for rgb_channel in each_pix.colors:
                encoding_file.write(int.to_bytes(rgb_channel, 1, byteorder='big', signed=False))


class Decoder:  # in charge of reading data from .ulbmp files. README : Chapter II.c.2

    @staticmethod
    def load_from(path: str) -> Image:

        with open(path, "rb") as file:
            header_base = file.read(5)  # len(U L B M P) = 5 bytes (1 per letter)
            if header_base != ULBMP_BYTES:
                raise ValueError("This file is not a valid .ulbmp file.")
            else:
                version = int.from_bytes(file.read(1), byteorder='big', signed=False)
                if version > LAST_VERSION:
                    raise NotImplementedError(f"Version not supported for now. Last one is {LAST_VERSION}.0")
                else:
                    header_bytes = file.read(2)  # header length is encoded on 2 bytes (little endian)
                    header_length = int.from_bytes(header_bytes, byteorder='little', signed=False)
                    expected_img_size_bytes = file.read(4)  # 2 bytes for the width, 2 for the height
                    if len(expected_img_size_bytes) != 4:
                        raise ValueError("Header data missing : no sufficient info to determine image size.")
                    # 'exp' stands for 'expected'
                    exp_width = int.from_bytes(expected_img_size_bytes[:2], byteorder='little')
                    exp_height = int.from_bytes(expected_img_size_bytes[2:], byteorder='little')

                    if version == 3:
                        last_header_infos = file.read(header_length - 12)  # excluding the previously read 12 bytes
                        # expecting 2 bytes for bbp and rle, then eventually 3 per palette color
                        bytes_per_pix, rle = last_header_infos[:2]
                        # Well, what could go wrong now ?
                        poss_faulty_vals = {len(last_header_infos) % 3 != 2 or len(last_header_infos) < 2 : 'header data',
                                                bytes_per_pix not in [1, 2, 4, 8, 24]: 'bits per pixel',
                                                rle not in [0, 1]: 'RLE'}
                        if any(failure for failure in poss_faulty_vals.keys()):
                            faulty_elems = [label for reason, label in poss_faulty_vals.items() if reason]
                            raise ValueError(f"{'/'.join(faulty_elems)} invalid for version 3 encoding.")
                            # Looks a bit silly, but it allows me to print out all the faulty values exhaustively.
                        else:
                            if rle and bytes_per_pix < 8:
                                raise NotImplementedError("RLE not supported for bit depths < 8."
                                                          f"Given depth is {bytes_per_pix}.")
                            if bytes_per_pix != 24:  # palette needed !
                                pix_palette = []
                                for byte_progress in range(2, len(last_header_infos), PIXEL_SUBELEMS):
                                    r, g, b = last_header_infos[byte_progress:byte_progress + PIXEL_SUBELEMS]
                                    pix_palette.append(Pixel(r, g, b))

                    remaining_data = file.read()  #... and we can now close the file safely.
        image_elems = []
        if version == 1 or (version == 3 and bytes_per_pix == 24 and not rle):
            final_exp_size = exp_width * exp_height * PIXEL_SUBELEMS  # 'exp' = expected
            if len(remaining_data) != final_exp_size:
                raise ValueError("Lack/overload of Pixel data." 
                                 f"Expected {final_exp_size} bytes, got {len(remaining_data)}.")
            else:
                for byte_progress in range(0, final_exp_size, PIXEL_SUBELEMS):
                    r, g, b = remaining_data[byte_progress: byte_progress + PIXEL_SUBELEMS]
                    image_elems.append(Pixel(r, g, b))

        elif version == 2 or (version == 3 and bytes_per_pix == 24 and rle):
            # 1 byte for number of consecutive occurences, 3 for RGB channels => 1 + 3
            if len(remaining_data) % (1 + PIXEL_SUBELEMS) != 0 or len(remaining_data) < 4:
                raise ValueError("Incomplete data for encoding following the pattern \"occurences +"
                                    f"rgb channels\" (version {version}.0).")
            else:
                for byte_progress in range(0, len(remaining_data), 1 + PIXEL_SUBELEMS):
                    occurences, r, g, b = remaining_data[byte_progress: byte_progress + 1 + PIXEL_SUBELEMS]
                    image_elems.extend([Pixel(r, g, b)] * occurences)

        elif version == 3 and bytes_per_pix < 24:  # v3, bpp < 24, rle = unknown
            # otherwordly said : if we have a palette in valid conditions...
            if not rle:
                for ind in range(len(remaining_data)):
                    pixs = remaining_data[ind]  # a byte
                    # see convertor.py for more details, README : Chapter II.d
                    refs_to_palette = Convertor.byte_evaluator(pixs, bytes_per_pix)
                    for ref in refs_to_palette:
                        image_elems.append(pix_palette[ref])

            elif rle and bytes_per_pix == 8:
                # 1 byte for each pixel's consecutive occurences, 1 for ref to palette
                if len(remaining_data) % 2 != 0 or len(remaining_data) < 2:
                    raise ValueError("Faulty image data for version 3 encoding with rle and bpp = 8.")
                for byte_progress in range(0, len(remaining_data), 2):
                    occurences, ref = remaining_data[byte_progress: byte_progress + 2]
                    # if there's a ref to a non-existent color
                    if ref >= len(pix_palette):
                        raise ValueError("Visibly lacking data in color palette. "
                                        f"Only {len(pix_palette)} colors available, "
                                        f"the given data needed access to color number {ref}.")
                    else:
                        image_elems.extend([pix_palette[ref]] * occurences)
            else:
                raise NotImplementedError("RLE not supported for bit depths < 8.")

        elif version == 4:
            # base pixel (this encoding is based on differences between pixels)
            last_pixel = Pixel(0, 0, 0)
            byte_progress = 0
            # While the image is not complete
            while byte_progress < len(remaining_data):
                last_r, last_g, last_b = last_pixel.colors
                byte = remaining_data[byte_progress]
                """
                IMPORTANT : you may notice weird substractions in the following lines.
                Like, a sudden '-2' from every difference in the 'SMALL DIFF' case.
                It's because the differences are encoded in a way that makes them
                strictly positive, and the decoding process must 'revert' that.
                I'll call these 'compensations' "[rgb]_neg_maker" (for "negative maker").
                """
                if byte == 0xff:  # signature = 11111111 (NEW PIXEL)
                    r, g, b = remaining_data[byte_progress + 1: byte_progress + 1 + PIXEL_SUBELEMS]
                    byte_progress += PIXEL_SUBELEMS

                # signature = 00xxxxxx (SMALL DIFF)
                elif byte >> 6 == 0b00:
                    rgb_neg_maker = 2
                    unused_00, diff_red, diff_green, diff_blue = Convertor.byte_evaluator(byte, shift_in_byte=2)
                    r, g, b = last_r + diff_red - rgb_neg_maker, \
                              last_g + diff_green - rgb_neg_maker, \
                              last_b + diff_blue - rgb_neg_maker

                # signature = 01xxxxxx (MEDIUM DIFF)
                elif byte >> 6 == 0b01:
                    g_neg_maker = 32
                    rb_neg_maker = 8
                    diff_green = (byte & 0b00111111) - g_neg_maker

                    byte_progress += 1
                    # reading the second byte to find the needed differences
                    dr_minus_dg, db_minus_dg = Convertor.byte_evaluator(remaining_data[byte_progress], shift_in_byte=4)
                    diff_red = dr_minus_dg + diff_green - rb_neg_maker
                    diff_blue = db_minus_dg + diff_green - rb_neg_maker
                    r, g, b = last_r + diff_red, last_g + diff_green, last_b + diff_blue

                # signature = 1xxxxxxx (BIG DIFF)
                elif byte >> 7 == 1:
                    diff_type_signature = byte >> 4  # makes the difference between the 3 cases
                    # Notice that in this case, the 'rgb_signed_diff' is already taken into account
                    # Within the Convertor.big_diff_rgb_evaluator method.
                    signature_to_col = {0b1000: "r", 0b1001: "g", 0b1010: "b"}  # essentially RGB_BIN_SIGNATURES_V4 reversed
                    r, g, b = Convertor.big_diff_rgb_evaluator({"r": last_r, "g": last_g, "b": last_b},
                                                                remaining_data[byte_progress:byte_progress + PIXEL_SUBELEMS],
                                                                signature_to_col[diff_type_signature])
                    byte_progress += 2  # 'jumping' above the 2 bytes used for the big differences
                else:
                    raise ValueError("Invalid image data.")

                byte_progress += 1  # moving on to the next byte for the next loop...
                pixel_res = Pixel(r, g, b)  # we got our pixel !
                image_elems.append(pixel_res)  # Let's add it to the list...
                last_pixel = pixel_res  # and we can carry on with the next pixel.

        else:
            raise ValueError("Invalid image data.")
        
        if len(image_elems) < exp_width * exp_height:
            raise ValueError(f"Incomplete image data for version {version} encoding.")
        elif len(image_elems) > exp_width * exp_height:
            image_elems = image_elems[: exp_width * exp_height]  # clearing up the "pseudo-pixels" (used for pading)

        return Image(exp_width, exp_height, image_elems)
