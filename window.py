"""
NOM : DEFOING
PRÉNOM : Daniel
SECTION : INFO
MATRICULE : 000589910
"""

# README : Chapter II.e


from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QHBoxLayout, \
                              QVBoxLayout, QFrame, QFileDialog, QErrorMessage, QDialog, QComboBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QColor, QPixmap
from encoding import Encoder, Decoder


LAST_VERSION = 4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # step 1 : window construction
        self.enabled_style = "background-color: rgb(80,80,80); color: white; font-family: Ubuntu; font-size: 12px;"
        self.disabled_style = "background-color: rgb(20,20,20); color: grey; font-family: Ubuntu; font-size: 12px;"
        self.window_base_setup()  # title, icon, geometry, max size, tooltip
        self.window_layout_setup()  # central widget, global layout, button layout, label
        self.buttons_placement(self.button_layout)  # creation + alignment : load_img_button, save_img_button
        self.separator_setup()
        self.combine_all(self.label, self.central_widget)  # finishing up global_layout and putting it in the window

        # step 2 : connections between buttons, file dialog, etc.
        self.load_img_button.clicked.connect(self.load_img_button_triggered)
        # main elements edited from here : self.image_to_show [Image] created, self.save_img_to_button enabled.
        # Calls image_decoding(self) that intializes self.decoded_image (using the Decoder.load_from() method)
        # then fills up a canvas and returns it to assign it to self.image_to_show.

        self.save_img_to_button.clicked.connect(self.save_image_button_triggered)
        # main elements edited from here : calls an instance of Dialog_encoding,
        # lets the user set the file to save their image to and an encoding version,
        # then calls the execute_save() method from the Dialog_encoding class if needed.

        self.img_info_button.clicked.connect(self.show_image_info_triggered)
        # Just creates a basic popup with the necessary info in it (image size + amount of unique colors)

    def window_base_setup(self):
        self.setWindowTitle("~ .ulbmp file manipulator ~")
        self.setWindowIcon(QIcon("ULB_ScientiaVT.png"))
        self.setGeometry(100, 100, 400, 400)
        self.setMinimumSize(330, 200)
        self.setStyleSheet("background-color: rgb(30,30,30); font-family: Ubuntu;"
                           "border: 1px solid grey; border-radius: 3px; color: white; font-size: 14px;")

    def window_layout_setup(self):
        self.central_widget = QWidget()  # Everything will be put in here
        self.global_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.label = QLabel("Click on \"Load\" to print out your .ulbmp file here")
        self.label.setStyleSheet("border: 1px solid rgb(40,40,40);")

    def buttons_placement(self, button_layout):
        # step 1 : components setup (creation + enabled/disabled + visuals)
        self.load_img_button = QPushButton("Load")
        self.save_img_to_button = QPushButton("Save")
        self.img_info_button = QPushButton("Image info")
        buttons = [self.load_img_button,self.save_img_to_button, self.img_info_button]
        for button in buttons:
            button.setFixedSize(90, 30)
            if button != self.load_img_button:
                button.setEnabled(False)
                button.setStyleSheet(self.disabled_style)
        self.load_img_button.setStyleSheet(self.enabled_style)

        # step 2 : adding components to the window
        for button in buttons:
            button_layout.addWidget(button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop | 
                                   Qt.AlignmentFlag.AlignLeft)
        self.global_layout.addLayout(button_layout, 0)  # the '0' parameter ensures that buttons will always
        # be at the top of the window, no matter how much it is resized.

    def separator_setup(self):
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.global_layout.addWidget(self.separator)

    def combine_all(self, label, central_widget):
        self.global_layout.addWidget(label, 100)
        self.global_layout.setAlignment(label, Qt.AlignmentFlag.AlignCenter)
        self.central_widget.setLayout(self.global_layout)
        self.setCentralWidget(central_widget)

    def load_img_button_triggered(self):
        options = QFileDialog.Options()
        absolute_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "ULBMP images(*.ulbmp)", options=options)
        if absolute_path:
            try:
                self.label.clear()  # clearing the previous image
                self.image_to_show = self.image_decoding(absolute_path)
                self.label.setPixmap(QPixmap.fromImage(self.image_to_show))  # image_to_show is a QImage
            except Exception as oops:
                self.show_exception(oops)  # Creates a QErrorMessage popup with the error message in it
            else:
                for button in [self.save_img_to_button, self.img_info_button]:
                    button.setEnabled(True)
                    button.setStyleSheet(self.enabled_style)
                self.load_img_button.setText("Load another...")
                # Resizing the window accordingly
                self.label.setFixedSize(self.image_to_show.size())
                if self.image_to_show.width() > 300:
                    self.setFixedWidth(self.image_to_show.width()+50)
                else:
                    self.setFixedWidth(300)
                if self.image_to_show.height() > 150:
                    self.setFixedHeight(self.image_to_show.height()+70)
                else:
                    self.setFixedHeight(150)

    def image_decoding(self, path):
        try:
            self.decoded_image = Decoder.load_from(path)
        except Exception as wait_what:
            self.show_exception(wait_what)
        else:
            w, h = self.decoded_image.ImgDimensions
            canvas_to_fill = QImage(w, h, QImage.Format_RGB888)  # blank canvas
            for y in range(h):
                for x in range(w):
                    r, g, b = self.decoded_image[x, y].colors
                    color = QColor(r, g, b)
                    canvas_to_fill.setPixelColor(x, y, color)
            return canvas_to_fill  #... now filled !

    def save_image_button_triggered(self):
        save_dialog_window = Dialog_encoding(self)
        save_dialog_window.image_to_be_saved = self.decoded_image
        save_dialog_window.show()

    def show_image_info_triggered(self):
        image_info = Image_Info_popup(self)
        image_info.show()

    def show_exception(self, exception_msg):
        error_dialog = QErrorMessage(self)
        error_dialog.setWindowTitle("Hmmm...")
        error_dialog.showMessage("Problem : " + str(exception_msg))


class Dialog_encoding(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid rgb(30,30,30); border-radius: 4px;")
        self.image_to_be_saved = None

        # step 1 : window construction
        self.window_and_layout_base()
        self.widget_additions()
        self.buttons_setup_save_UI()
        self.selected_option = "1.0"  # by default
        self.setLayout(self.layout)

        # step 2 : connections
        self.destination_choice.clicked.connect(self.choose_destination)
        self.encoding_type.currentIndexChanged.connect(self.encoding_type_changed)
        self.change_rle.stateChanged.connect(lambda : self.rle_changed())
        self.confirm_button.clicked.connect(lambda : self.execute_save(self.my_path.text(), 
                                                                       self.selected_option, self.image_to_be_saved))
        # Not a fan of these 2 lambda functions, but I'm not sure how to do otherwise...

    def window_and_layout_base(self):
        self.setWindowTitle("~ Image saving options ~")
        self.setGeometry(100, 100, 500, 200)
        self.setFixedSize(500, 400)
        self.layout = QVBoxLayout()
        self.base_text = QLabel("Current encoding path :")
        self.my_path = QLabel("[no path selected]")
        for text in [self.base_text, self.my_path]:
            text.setFixedHeight(30)
            text.setAlignment(Qt.AlignmentFlag.AlignTop |
                              Qt.AlignmentFlag.AlignLeft)
        self.destination_layout = QHBoxLayout()
        self.encoding_layout = QHBoxLayout()
        self.rle_layout = QHBoxLayout()
        self.bpp_layout = QHBoxLayout()

    def widget_additions(self):
        self.layout.addWidget(self.base_text)
        self.layout.addWidget(self.my_path)
        for sub_layout in [self.destination_layout, self.encoding_layout, self.rle_layout, self.bpp_layout]:
            self.layout.addLayout(sub_layout)

    def buttons_setup_save_UI(self):
        # step 1 : components set up
        self.destination_choice = QPushButton("Browse")
        self.destination_choice.setFixedSize(200, 50)
        self.destination_text = QLabel("Select a file...")
        self.encoding_type = QComboBox()  # dropdown menu
        self.encoding_type.setFixedSize(200, 50)

        for encoding in range(1, LAST_VERSION + 1):
            self.encoding_type.addItem(str(float(encoding)))

        self.encoding_text = QLabel("Encoding type :")
        self.change_rle = QCheckBox()
        self.change_rle.setStyleSheet("QCheckBox::indicator{width : 40px;height : 40px;}")
        self.rle_text = QLabel("RLE :")
        self.bits_per_pixel = QComboBox()
        self.bits_per_pixel_text = QLabel("Bytes per pixel :")
        for button, text in [(self.destination_choice, self.destination_text), 
                             (self.encoding_type, self.encoding_text),
                             (self.change_rle, self.rle_text), 
                             (self.bits_per_pixel, self.bits_per_pixel_text)]:
            button.setFixedSize(200, 50)
            text.setFixedSize(200, 50)
            if text == self.bits_per_pixel_text or text == self.rle_text:
                button.setEnabled(False)
                text.setStyleSheet("color: grey;")

        depths = ["1", "2", "4", "8", "24"]
        for depth in depths:
            self.bits_per_pixel.addItem(depth)
        self.confirm_button = QPushButton("Confirm all and save")
        self.confirm_button.setStyleSheet(self.parent().disabled_style)
        for button in [self.destination_choice, self.confirm_button, self.encoding_type]:
            button.setStyleSheet(self.parent().enabled_style)
        self.bits_per_pixel.setStyleSheet(self.parent().disabled_style)

        # step 2 : adding components to the window
        # layout, text, button = group
        lay_tex_but_groups = [(self.destination_layout, self.destination_text, self.destination_choice),
                              (self.encoding_layout,self.encoding_text, self.encoding_type),
                              (self.rle_layout, self.rle_text, self.change_rle),
                              (self.bpp_layout, self.bits_per_pixel_text, self.bits_per_pixel)]
        for layout, text, button in lay_tex_but_groups:
            layout.addWidget(text)
            layout.addWidget(button)
            text.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.confirm_button)
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet(self.parent().disabled_style)

    def encoding_type_changed(self, index):
        self.selected_option = self.encoding_type.itemText(index)
        is_ver3 = self.selected_option == "3.0"
        self.change_rle.setEnabled(is_ver3)
        if is_ver3:  # quick trigger to 'refresh' bpp values available
            self.change_rle.setChecked(True)
            self.change_rle.setChecked(False)
            bpp_rle_color = "color: white;"
            bpp_style_sheet = self.parent().enabled_style
        else:
            bpp_rle_color = "color: grey;"
            bpp_style_sheet = self.parent().disabled_style
            
        self.bits_per_pixel.setEnabled(is_ver3)
        self.rle_text.setStyleSheet(bpp_rle_color)
        self.bits_per_pixel_text.setStyleSheet(bpp_rle_color)
        self.bits_per_pixel.setStyleSheet(bpp_style_sheet)

    def rle_changed(self):
        last_selected = self.bits_per_pixel.currentText()
        self.bits_per_pixel.clear()  # clearing all previous possible choices
        if self.change_rle.isChecked():
            if 2**8 >= self.image_to_be_saved.color_count:
                self.bits_per_pixel.addItem("8")
            self.bits_per_pixel.addItem("24")
            if last_selected not in ["1", "2", "4"]:
                self.bits_per_pixel.setCurrentIndex(self.bits_per_pixel.findText(last_selected))

        else:
            for depth in ["1", "2", "4", "8"]:
                if 2**int(depth) >= self.image_to_be_saved.color_count:
                    self.bits_per_pixel.addItem(depth)
            self.bits_per_pixel.addItem("24")
            self.bits_per_pixel.setCurrentIndex(self.bits_per_pixel.findText(last_selected))

    def choose_destination(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
                       self, "Choose a file to overwrite the data of", "", "ULBMP images(*.ulbmp)", options=options)
        if file_name:
            # In a previous version, you could overwrite any file - pretty funny, but *kinda* dangerous ¯\_(ツ)_/¯
            text_to_display = "We're good to go!"
            self.my_path.setText(file_name)
            self.destination_text.setText(text_to_display)
            self.confirm_button.setEnabled(True)
            self.confirm_button.setStyleSheet(self.parent().enabled_style)

    def execute_save(self, path, version, image):
        version = int(version[0])
        if version == 3:
            rle = self.change_rle.isChecked()
            bpp = int(self.bits_per_pixel.currentText())
            image_config = Encoder(image, version, rle=rle, depth=bpp)
        else:
            image_config = Encoder(image, version)
        try:
            image_config.save_to(path)
        except Exception as hmmm_what_happened:
            self.parent().show_exception(hmmm_what_happened)

        else:
            self.close()  # we're done with the saving process !
            # note that this operation may look a bit... abrupt to the user, in the cases where the
            # saving gets done super fast (the save window shuts down brutally). 
            # Just keep in mind that no error message = no error detected whatsoever.


class Image_Info_popup(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.window_and_layout_base()
        self.setLayout(self.layout)

    def window_and_layout_base(self):
        self.setWindowTitle("~ Image info ~")
        self.setGeometry(150, 150, 300, 150)
        self.setFixedSize(300, 150)
        self.layout = QVBoxLayout()
        w, h = self.parent().decoded_image.ImgDimensions
        base_style = "color: white; font-family: Ubuntu; font-size: 20px;" \
                    "border: 1px solid rgb(40,40,40); border-radius: 3px;"
        self.display_img_size = QLabel(f"Image size : {w} x {h}")
        self.display_img_size.setStyleSheet(base_style)
        self.display_colors_amount = QLabel(f"Number of colors : {self.parent().decoded_image.color_count}")
        self.display_colors_amount.setStyleSheet(base_style)
        self.layout.addWidget(self.display_img_size)
        self.layout.addWidget(self.display_colors_amount)
