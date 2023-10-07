# Import necessary modules
from frontend import Ui_MainWindow
import sys
from PyQt5 import QtCore, QtWidgets, QtGui, QtSvg
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QPixmap
import json
import sqlite3
import requests
import numpy as np
import difflib
import news_search as ns


# Create the main class inheriting from QMainWindow and Ui_MainWindow
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(__class__, self).__init__()
        self.setupUi(self)
        # Set window properties
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.showFullScreen()
        self.stackedWidget.setCurrentIndex(0)

        # Initialize variables
        self.hover_flag = False
        self.top_news_cards_counter = 0
        self.suggestion_cards_counter = 0
        self.fresh_start = True
        self.cards_clear = False
        self.search = False

        self.preference = []
        self.current_news = 0

        # Connect button signals to functions
        self.pushButton_like.clicked.connect(lambda: self.liked(self.current_news))
        self.pushButton_8.clicked.connect(lambda: self.closing())
        self.pushButton_7.clicked.connect(lambda: self.showMinimized())

        cat_list = ["BUSINESS", "TECH", "WORLD NEWS", "SPORTS", "ENTERTAINMENT"]
        self.pushButton_0.clicked.connect(lambda: self.set_type_name(None, None))
        self.pushButton_1.clicked.connect(lambda: self.set_type_name(cat_list[0], 1))
        self.pushButton_2.clicked.connect(lambda: self.set_type_name(cat_list[1], 2))
        self.pushButton_3.clicked.connect(lambda: self.set_type_name(cat_list[2], 3))
        self.pushButton_4.clicked.connect(lambda: self.set_type_name(cat_list[3], 4))
        self.pushButton_5.clicked.connect(lambda: self.set_type_name(cat_list[4], 5))
        self.pushButton_6.clicked.connect(lambda: self.set_type_name(None, 6))

        # Initialize SVG widget
        self.widget = QtSvg.QSvgWidget(self.frame_title_image)
        self.widget = QtSvg.QSvgWidget("news_title_image.svg")
        self.widget.setMinimumSize(QtCore.QSize(640, 640))
        self.widget.setObjectName("widget")
        self.verticalLayout_17.addWidget(
            self.widget, 1, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
        )

        # Initialize database
        self.initiate_database()
        self.set_type_name()

    def set_type_name(self, name=None, serial=None):
        self.search = False
        # Reset button styles
        for i in range(0, 6):
            exec(
                f"""self.pushButton_{i}.setStyleSheet('''
            QPushButton{{background: rgb(245, 245, 245); border-radius: 24px; padding: 16px; }}
            QPushButton::hover{{background: rgb(240, 240, 240); border-radius: 24px; padding: 16px; }}
            QPushButton::pressed{{background: rgb(235, 235, 235); border-radius: 24px; padding: 16px; }}''')"""
            )
        # Check if the user selected a category or it's a fresh start
        if serial is None:
            self.fresh_start = True
            self.cards_clear = True
            self.news_initiate()
            exec(
                f"""self.pushButton_{0}.setStyleSheet("background: rgb(205, 205, 205); border-radius: 24px; padding: 16px;")"""
            )
        elif serial == 6:
            self.search = True
            self.fresh_start = True
            self.cards_clear = True
            self.news_initiate()

        else:
            self.news_initiate(name)
            exec(
                f"""self.pushButton_{serial}.setStyleSheet("background: rgb(205, 205, 205); border-radius: 24px; padding: 16px;")"""
            )

    def initiate_database(self):
        # Connect to SQLite database
        self.conn = sqlite3.connect("mini_project_ds.db", check_same_thread=False)
        self.c = self.conn.cursor()
        self.c.execute("SELECT * FROM news")
        self.news = self.c.fetchall()
        self.conn.commit()

        self.all_categories = []

        # Extract news categories from database
        for i in range(len(self.news)):
            val = list(self.news[i][15:56])
            self.all_categories.append(val)

        try:
            # Load user preferences from JSON file
            with open("preference.json", "r") as f:
                self.preference = json.load(f)
        except:
            pass

    def news_initiate(self, name=None):
        # Check if there is a preference or not
        if self.preference != []:
            # Check if it is a fresh start or not
            if self.fresh_start == True:
                reference_list = [
                    sum(pair) / len(pair) for pair in zip(*self.preference)
                ]

                self.fresh_start = False
                if self.cards_clear:
                    self.news_clear()
                    self.suggestion_card_clear()
            else:
                try:
                    reference_list = self.create_list(name)
                    self.news_clear()
                    self.suggestion_card_clear()
                except:
                    pass

            sorted_indices = self.sort_list_indexes_closest_to_reference(
                self.all_categories, reference_list
            )
            # Check if there is a search query or not
            if self.search == True and self.lineEdit_2.text() != "":
                sorted_indices = ns.article_score(
                    self.lineEdit_2.text(), len(sorted_indices)
                )
            # Initiate the news cards beased on sorted indices
            for i in sorted_indices:
                self.initiate_top_news_cards(i)
            # Initiate the suggestions based on top 5 sorted indices
            sorted_indices_2 = sorted_indices[0:5]
            for i in sorted_indices_2:
                self.initiate_suggestion_cards(i)

            # Forgot why i did that, but does not seem to effect the code so far, but not deleting either
            # sorted_indices = [int(x) for x in sorted_indices]
            # sorted_indices.sort()

        else:
            for i in range(len(self.news)):
                self.initiate_top_news_cards(i)

    # Creates a reference list based on similarity ration when clicked on one the categories
    def create_list(self, name):
        col_names = [desc[0] for desc in self.c.description]
        col_names = col_names[15:56]
        new_list = []
        for n in col_names:
            # calculate the similarity ratio between name and n
            ratio = difflib.SequenceMatcher(None, name, n).ratio()
            # if the ratio is greater than or equal to 0.8, assign 99 to the list
            if ratio >= 0.8:
                new_list.append(99)
            # otherwise, assign 0 to the list
            else:
                new_list.append(0)
        return new_list

    # Opens a news in the news feed
    def open_news(self, num):
        try:
            # Change all the UI attributes for the news
            self.stackedWidget.setCurrentIndex(1)
            self.current_news = num
            self.label_title.setText(self.news[num][1])
            self.label_content.setText(
                f"<b>{self.news[num][8]}</b>  -  {self.news[num][7]}"
            )
            self.label_footer.setText(
                f"This story was collected from: <b>{self.news[num][10]}</b>"
            )
            image_url = self.news[num][9]
            # Try to download the news image
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open("news_image.jpg", "wb") as file:
                        file.write(response.content)

                pixmap = QPixmap("news_image.jpg")
                pixmap = pixmap.scaled(
                    self.label_image.width(),
                    self.label_image.width(),
                    QtCore.Qt.KeepAspectRatio,
                )
                self.label_image.setPixmap(pixmap)

            except:
                self.label_image.setText("Error loading image")

        except:
            self.label_image.setText("Error loading News")
        # Clear old suggestion cards
        if self.suggestion_cards_counter != 0:
            self.suggestion_card_clear()

        # Find new reference list and suggestion cards for the current news
        reference_list = self.all_categories[num]
        sorted_indices = self.sort_list_indexes_closest_to_reference(
            self.all_categories, reference_list
        )
        sorted_indices = sorted_indices[1:6]
        for i in sorted_indices:
            self.initiate_suggestion_cards(i)

    # Doing what the name suggests
    def sort_list_indexes_closest_to_reference(self, all_categories, reference_list):
        all_categories_array = np.array(all_categories)
        reference_list_array = np.array(reference_list)
        distances = np.linalg.norm(all_categories_array - reference_list_array, axis=1)
        sorted_indexes = np.argsort(distances)

        return sorted_indexes

    # Adding a news to the preference list when liked in clicked
    def liked(self, num):
        self.pushButton_like.setText("Liked")
        self.preference.append(self.all_categories[num])

    # Saving the preference list to a JSON before closing
    def closing(self):
        with open("preference.json", "w") as f:
            # Dump the list as a json object into the file
            json.dump(self.preference, f)

        self.close()

    # Clearing out all the suggestion cards
    def suggestion_card_clear(self):
        for i in range(self.suggestion_cards_counter):
            try:
                exec(f"self.frame_suggestion_{i+1}.deleteLater()")
                exec(f"self.label_suggestion_{i+1} = None")
            except:
                pass

        self.suggestion_cards_counter = 0

    # Clearing out all the top news cards
    def news_clear(self):
        for i in range(self.top_news_cards_counter):
            try:
                exec(f"self.frame_top_news_{i+1}.deleteLater()")
                exec(f"self.label_headline_{i+1} = None")
            except:
                pass

        self.top_news_cards_counter = 0

    # When the mouse is hovering over a news/suggestion card
    def mouse_hover(self, flag, num=None, card_num=None, suggestion_clicked=False):
        self.hover_flag = flag
        self.headline_number = num
        self.active_card = card_num
        self.suggestion_active = suggestion_clicked

    # When the mouse is pressed on a news/suggestion card
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.hover_flag == True:
            self.pushButton_like.setText("Like")
            self.open_news(self.headline_number)

            for i in range(len(self.news)):
                exec(
                    f"""self.frame_top_news_{i+1}.setStyleSheet("background: white;")"""
                )
            if self.suggestion_active == False:
                exec(
                    f"""self.frame_top_news_{self.active_card}.setStyleSheet("background: rgb(225, 225, 225);")"""
                )

    # Initiating the news cards
    def initiate_top_news_cards(self, num):
        self.top_news_cards_counter += 1

        self.frame_top_news_ = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame_top_news_.setStyleSheet("background: white;")
        self.frame_top_news_.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_top_news_.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_top_news_.setObjectName("frame_top_news_")
        self.verticalLayout_18 = QtWidgets.QVBoxLayout(self.frame_top_news_)
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.label_headline_ = QtWidgets.QLabel(self.frame_top_news_)
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Static Small ")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_headline_.setFont(font)
        self.label_headline_.setWordWrap(True)
        self.label_headline_.setObjectName("label_headline_")
        self.verticalLayout_18.addWidget(self.label_headline_)
        self.verticalLayout_13.addWidget(self.frame_top_news_)

        self.frame_top_news_.setObjectName(
            f"frame_top_news_{self.top_news_cards_counter}"
        )
        self.label_headline_.setObjectName(
            f"label_headline_{self.top_news_cards_counter}"
        )
        setattr(
            self, f"frame_top_news_{self.top_news_cards_counter}", self.frame_top_news_
        )
        setattr(
            self, f"label_headline_{self.top_news_cards_counter}", self.label_headline_
        )
        card_num = self.top_news_cards_counter
        self.label_headline_.enterEvent = lambda event: self.mouse_hover(
            True, num, card_num, False
        )
        self.label_headline_.leaveEvent = lambda event: self.mouse_hover(False)

        self.label_headline_.setText(self.news[num][1])

    # Initiating the suggestion cards
    def initiate_suggestion_cards(self, num):
        self.suggestion_cards_counter += 1

        self.frame_suggestion_ = QtWidgets.QFrame(self.frame_suggest)
        self.frame_suggestion_.setStyleSheet("background: white;")
        self.frame_suggestion_.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_suggestion_.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_suggestion_.setObjectName("frame_suggestion_")
        self.verticalLayout_19 = QtWidgets.QVBoxLayout(self.frame_suggestion_)
        self.verticalLayout_19.setObjectName("verticalLayout_19")
        self.label_suggestion_ = QtWidgets.QLabel(self.frame_suggestion_)
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Static Small ")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_suggestion_.setFont(font)
        self.label_suggestion_.setWordWrap(True)
        self.label_suggestion_.setObjectName("label_suggestion_")
        self.verticalLayout_19.addWidget(self.label_suggestion_)
        self.verticalLayout_7.addWidget(self.frame_suggestion_)
        self.verticalLayout_7.addWidget(self.frame_suggestion_, 0, QtCore.Qt.AlignTop)

        # Adding unique names to the objects
        self.frame_suggestion_.setObjectName(
            f"frame_suggestion_{self.suggestion_cards_counter}"
        )
        self.label_suggestion_.setObjectName(
            f"label_suggestion_{self.suggestion_cards_counter}"
        )
        # Setting attributes
        setattr(
            self,
            f"frame_suggestion_{self.suggestion_cards_counter}",
            self.frame_suggestion_,
        )
        setattr(
            self,
            f"label_suggestion_{self.suggestion_cards_counter}",
            self.label_suggestion_,
        )

        # Initiate mouse hovering
        card_num = self.suggestion_cards_counter
        self.label_suggestion_.enterEvent = lambda event: self.mouse_hover(
            True, num, card_num, True
        )
        self.label_suggestion_.leaveEvent = lambda event: self.mouse_hover(False)

        self.label_suggestion_.setText(self.news[num][1])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Main()
    form.show()
    sys.exit(app.exec_())
