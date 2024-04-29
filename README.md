Quick note before we start - you can always hide any chapter or section by clicking on the little arrow of the left of each line in your editor (works with most code editors and note-taking apps that support markdown (the vast majority of them), like [Obsidian](https://obsidian.md/), [Notion](https://www.notion.so/), [RemNote](https://www.remnote.com/), [SiYuan (the one I use)](https://b3log.org/siyuan/en/)...).  
*<u>Any</u>* reference to this README doc within the project files can be found using the `Ctrl + F + "README"`​ command.

* **<u>TABLE OF CONTENTS</u>**

  * *I. What was this project useful for ?*
  * *II. Brief overview of the project files*

    * a. `pixel.py`​​
    * b. `image.py`​​
    * c. `encoding.py`​​

      * Main methods

        1. ​`save_to`​​
        2. ​`load_from`​​
      * Additional Info

        * A. About the encoding/decoding method for `ULBMP 4.0`​​ - value handling
    * d. `convertor.py`​​

      * Main methods

        1. ​`byte_evaluator`​​
        2. ​`byte_maker`​​
        3. ​`big_diff_rgb_evaluator`​​
        4. ​`big_diff_rgb_maker`​​
    * e. `window.py`​​
    * f. `main.py`​ [no comment needed]
  * *III. Sources*

    ---
  * <u>*I. What was this project useful for ?*</u>

    * To keep it simple, it was a part of a first-year course at the ULB (an university in Belgium), and the end goal was to produce a new image format (`.ulbmp`​) using well-known image compression methods, like referencing a *color palette* ([(1)](https://codehs.com/editor/hoc/540995/4368/3117)), defining a certain *pixel depth,*  making use of *Real Length Encoding* ([(2)](https://www.csfieldguide.org.nz/en/chapters/coding-compression/run-length-encoding/)), or even taking inspiration from the QOI (*Quite Ok Image*) format ([(3)](https://qoiformat.org/)).  
      The project was split in several *versions* (from $1.0$ to $4.0$) that would build upon eachother, like a pyramid (or like many apps we all use daily).
    * All of this had to be supported by an User Interface we would create ourselves using PySide6 ([(4)](https://doc.qt.io/qtforpython-6/)). So in essence, we got pretty much thrown into the deep end of the pool, with this project being the first one to require :

      * to learn a full library by ourselves (PySide6)
      * to make a "True" graphical interface
      * to manipulate binary data (and files in general) to this extent
      * ...
  * *<u>II. Brief overview of the project files</u>*

    * a. `pixel.py`​​​

      * Desc : Gives the template of the info contained in a single pixel (RGB values), and notably defines the `__eq__`​ and `__hash__`​ methods for easier `set()` manipulations later on. See documetation to learn more about these methods : [(5)](https://docs.python.org/3/library/operator.html)
    * b. `image.py`​​​

      * Desc : Built upon `pixel.py`​​, defines how to actually *perceive* an Image in this project : a linear list of `Pixel()`​​ instances of a given `width*height`​​ size.
      * Includes explicitely defined getters and setters - especially to find a specific `Pixel()`​​ using $[x,y]$ coordinates (even though the list is linear (one-dimensional)).
    * c. `encoding.py`​​​

      * Main methods

        1. ​`save_to`​​​ (from the `Encoder`​​​ class)

            * Working in tandem with the `load_from`​​ method from the `Decoder`​​ class (see below), writes the binary content of any `.ulbmp`​​ file. I'll go more in depth on how a `.ulbmp`​​ file works in the "Additionnal info" section (further down in this Chapter - II.c.A), but just keep in mind that a `.ulbmp`​​ file is "recognizable" via its specific header (*i.e* starts with `ULBMP`​​ written in binary, then other specifications).
            * A quick note over the usage of a *color palette* for certain instances of `ULBMP 3.0`​ : an intuitive way of "visualizing a painter's palette in code" is to use a *list* of colors, with our "colors" being *representative* `Pixel()`​ instances.  
              So in essence, after encoding that *list of colors*, each piece of data that represents a pixel is actually a *reference to a certain index in the palette*. For instance, if my `palette[0] = Pixel(0,0,0)`​ (pitch black pixel) and I decide to encode each *reference* *to the palette* on 8 bits, then a reference like `00000000`​ means that the index of my palette this reference points towards is `0`​ (the pitch black pixel).
            * Another remark over the encoding/decoding process specifically in `ULBMP ver. 4.0`​. As previously said, it is heavily inspired by the *Quite Ok Image* format ([(3)](https://qoiformat.org/)), but it has been toned down a little. In this project, the *only* thing that matters is the difference between the previous pixel and the one we're currently encoding/reading ; it is then only logical to begin with a "base pixel" (pitch black by defaut - `Pixel(0,0,0)`​) to start calculating *differences* from the very first pixel onwards. All the "difference cases" are explicit enough in the project file.
        2. ​`load_from`​ (static ([(6)](https://docs.python.org/3/library/functions.html#staticmethod)), from the `Decoder`​ class)

            * Works similarly to the `save_to`​ method from the `Encoder`​ class (see above), but instead reads the data of a given file. It is in charge of reading lots of info, like header data, image size, the palette if there's one, etc - all of this to return an `Image()`​ instance (see `image.py`​, Chapter II.b).
            * There's not much to say that hasn't been said in the corresponding project file - apart from the fact that I suggest u to read the `Encoder`​​ class before the `Decoder`​​ one to get a better grasp at how all of this works *as a tandem*.
      * Additionnal info

        * A.  About the encoding/decoding method for `ULBMP 4.0`​​ - value handling

          * Every single value in an `.ulbmp`​​​ file is positive. However, when reading *differences between pixels* (specific to version $4.0$), it is only logical to think that negative differences can exist : this is why, when *<u>decoding</u>* a file of this type, we must apply "magical" *substractions* to our found values in order to find the "True" differences. The same principle applies for the *<u>encoding</u>* process - but in reverse : when we find out that there's a negative difference between 2 neighbouring pixels' colors, we must apply an *addition* to get a positive value no matter the difference.
          * So I wrote all of this for u not to be surprised by the "magic numbers" (depicted as `[rgb]_pos_makers`​​ and `[rgb]_neg_makers`​​ for "positive/negative makers") u might find in the project files. Just take another look at the difference *condition* (the `if...elif`​​ part) and u will find out that these "magical operations" are the *compensations* u would expect to make all the values positive.
    * d. `convertor.py`​​

      * Desc : Applies varied operations from its unique `Convertor`​​ class. "Specialized" in byte manipulation : either reads values from a set of given bytes or calculates integers to be converted into bytes for encoding purposes.
      * Main methods

        1. ​`byte_evaluator`​

            * As said in the corresponding project file, returns a list of "references" to a color palette (specific to $3.0$ version, see Chapter II.c.1). For instance, if we suppose that each reference to the palette is on 4 bits and that we must read the byte $b = 00001111$, then $b$ must be read as $0000 \space \space 1111$ ; it contains the references to `palette[0]`​​​ ($0000$ in binary) and to `palette[15]`​​​ ($1111$ in binary).
        2. ​`byte_maker`​

            * The previous method's "duo". From a given list of `Pixel()`​ instances and a list of unique colors (a palette), creates the value (an integer, but to visualize as a byte) to be encoded.
        3. ​`big_diff_rgb_evaluator`​

            * You can see how a "Big Diff" is defined within the project files (notably `Encoder.save_to`​​ and `Decoder.load_from`​​ from `encoding.py`​​). This method was created solely to read a set of 3 bytes and extract the color differences from them. This operation is necessary to define the final values of each `Pixel()`​​'s colors when decoding.
        4. ​`big_diff_rgb_maker`​​

            * If u have understood how the `big_diff_rgb_evaluator`​​ method works and why it exists, this one should be clear ; it just reverts the process seen in `big_diff_rgb_evaluator`​​.
    * e. `window.py`​

      * Desc : the part where the UI is created and is immediately shown when `main.py`​ is executed.
      * You may notice that quite a lot of methods are called when the constructor gets initialized (like `self.window_base_setup()`​, `self.window_layout_setup()`​, `self.buttons_placement(self.button_layout)`​...). These functions are only called once each, and it's normal : their only purpose is to avoid having a constructor fulfilled with "overwhelming details".  
        Like, if u don't have experience at all with PySide6 ([(4)](https://doc.qt.io/qtforpython-6/)), this code provides a structured example on how to initialize a proper window (without having a 100-lines long constructor that would discourage any beginner - including myself), and if u have more experience, u can skip reading these functions entirely in order to get right to the "interesting part" (the more "implementation-specific" features).
      * Every class in the file follows this logic, and the 3 present classes are ordered by "importance" : `MainWindow(QMainWindow)`​ obviously comes first, followed by `Dialog_encoding(QDialog)`​ that only shows up under certain conditions, and the last one is `Image_Info_popup(QDialog)`​ because it's just a popup with no interaction possible.
    * f. `main.py`​ [no comment needed]
  * *<u>III. Sources - all last consulted on March 5</u>*​*<u>^th^</u>*​ *<u>, 2024 (2:37 PM)</u>*

    1. [CodeHS - colors in bits](https://codehs.com/editor/hoc/540995/4368/3117)
    2. [CSFieldGuide - Coding - Compression - Chap. 7.2 : Run length encoding](https://www.csfieldguide.org.nz/en/chapters/coding-compression/run-length-encoding/)
    3. [The Quite OK Image Format for Fast, Lossless Compression](https://qoiformat.org/)
    4. [Qt for Python - official doc](https://doc.qt.io/qtforpython-6/)
    5. [Python 3.12 official doc - operators - Standard operations as functions](https://docs.python.org/3/library/operator.html)
    6. [Python 3.12 official doc - built-in functions - @staticmethod](https://docs.python.org/3/library/functions.html#staticmethod)

‍
