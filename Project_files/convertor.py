"""
NOM : DEFOING
PRÉNOM : Daniel
SECTION : INFO
MATRICULE : 000589910
"""

# README : Chapter II.d


from pixel import Pixel


class Convertor:
    @staticmethod
    def byte_evaluator(val: int, shift_in_byte: int) -> list:
        """
        Returns a list with every value found "per x bits" (from left to right) ; 
        i.e. with a shift in byte of 4, it will return 8/4 = 2 values
        (the value on the 4 first bits followed by the one on the 4 last).
        Try to visualize "val" as a byte (rather than an integer in base 10)
        README Chapter II.d.1
        """
        tot_values = []
        for nth_bit in range(7, -1, -shift_in_byte):  # iterating on bits from left to right
            current_value = 0
            exponent = shift_in_byte - 1
            for subshift in range(nth_bit, nth_bit - shift_in_byte, -1): # finding the needed group of bits
                bit = (val & (1 << subshift)) >> subshift 
                current_value += bit << exponent # equivalent to 'current_value += bit * 2 ** exponent'
                exponent -= 1
            tot_values.append(current_value)
        return tot_values
    
    @staticmethod
    def byte_maker(pixels_to_convert: list, bits_per_pixel: int, unique_colors : list[Pixel]) -> int:
        """
        The 'complement' of the previous method ; makes one byte from a sublist of pixels, taking bpp into
        account and referencing the unique_colors' list the right way.
        README Chapter II.d.2
        """
        while len(pixels_to_convert) < 8 // bits_per_pixel:  # while we lack pixels
            pixels_to_convert.append(unique_colors[0])  # pading
        val = 0
        for pixel in pixels_to_convert:
            val = val << bits_per_pixel  # shift everything we currently have to make space for the next ref
            val += unique_colors.index(pixel)  # find the ref to the palette
        return val
    
    @staticmethod
    def big_diff_rgb_evaluator(last_colors : dict, data : list[bytes], base_diff_color : str)-> tuple[int, int, int]:
        """
        Just as seen above, this method is part of a 'duo' with the one below. It extracts the rgb values from
        a given set of 3 bytes (composed of a signature, a main difference and two "equations" of differences).
        See README (Chapter II.d.3).
        (You may notice 'magical' substractions and additions in this ; refer to encoding.py "Decoder.load_from" and
        "Encoder.save_to" methods and README Chapter II.c.A for an in-depth explanation of this.)
        """
        conversion_dict = {"r":["g", "b"], "g":["r", "b"], "b":["r", "g"]}
        finale = {"r":0, "g":0, "b":0}
        diff_to_truecol1 = 128
        diff_to_truecols2and3 = 32
        four_first = (data[0] & 0b00001111) << 4  # '4 first' because the first diff is on 8 bits, split among 2 bytes
        four_last = data[1] >> 4
        color_1_diff = four_first + four_last - diff_to_truecol1
        finale[base_diff_color] = last_colors[base_diff_color] + color_1_diff

        diff_2_four_first = (data[1] & 0b00001111) << 2
        diff_2_two_last = data[2] >> 6

        diff_2 = diff_2_four_first + diff_2_two_last - diff_to_truecols2and3
        diff_3 = (data[2] & 0b00111111) - diff_to_truecols2and3
        col2, col3 = conversion_dict[base_diff_color]
        
        finale[col2] = last_colors[col2] + color_1_diff + diff_2
        finale[col3] = last_colors[col3] + color_1_diff + diff_3

        return (finale["r"], finale["g"], finale["b"])

    def big_diff_rgb_maker(diffs : dict, main_color_and_signature : list[str, int]) -> list[bytes]:
        """
        Creates a value (technically an integer, but see it more as a value on 3 bytes)
        to be written in the encoding_file (see encoding.py and README, Chapter II.d.4).
        Main structure (syntax : value, (bits)):
        signature (4) + main_color_diff (8) + diff_2 (6) + diff_3 (6).

        Diff 2 and diff 3 can be deducted from the "conversion_dict" (I could've set it as
        a global constant, but putting it right here helps to visualize the situation better).
        :param diffs: structured like {"r":diff_red, "g":diff_green, "b":diff_blue}.
        """
        conversion_dict = {"r":["g", "b"], "g":["r", "b"], "b":["r", "g"]}
        color_key, signature = main_color_and_signature
        final_val = (signature << 20) + \
                    (diffs[color_key] + 128 << 12) + \
                    (diffs[conversion_dict[color_key][0]] - diffs[color_key] + 32 << 6) + \
                    (diffs[conversion_dict[color_key][1]] - diffs[color_key] + 32)
        # Situation after each line of the addition (syntax : value, (bits)) :
        # signature (4) + ??? (20)
        # signature (4) + main_color_diff (8) + ??? (12)
        # signature (4) + main_color_diff (8) + diff_2 (6) + ??? (6)
        # signature (4) + main_color_diff (8) + diff_2 (6) + diff_3 (6)
        return final_val
    