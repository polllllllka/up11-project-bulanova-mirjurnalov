from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import os

class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.main_window = None
        
        self.setWindowTitle("Авторизация - Мир журналов")
        self.resize(350, 200)
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(BASE_DIR, "resources", "Мир журналов.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet("""
            QWidget { background-color: #FFFFFF; font-family: Calibri; }
            QLabel { font-size: 14px; color: #000000; }
            QLineEdit { font-size: 14px; padding: 5px; border: 1px solid #ccc; }
            QPushButton { 
                background-color: #70B2AF; color: #000000; 
                font-weight: bold; padding: 8px; border-radius: 4px; font-size: 14px; 
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("Вход в систему")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addWidget(QLabel("Введите логин (без пароля):"))
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("admin, manager1, client01...")
        layout.addWidget(self.login_input)
        
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.try_login)
        layout.addWidget(self.btn_login)
        
        self.btn_guest = QPushButton("Войти как гость")
        self.btn_guest.setStyleSheet("background-color: #D2F6E7;")
        self.btn_guest.clicked.connect(self.login_as_guest)
        layout.addWidget(self.btn_guest)

    def try_login(self):
        login = self.login_input.text().strip()
        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин!")
            return
            
        user_data = self.db.check_login(login)
        
        if not user_data:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден!")
            return
            
        user_id, role_id, last_name, first_name, middle_name, role_name = user_data
        
        full_name = f"{last_name} {first_name}"
        if middle_name:
            full_name += f" {middle_name}"
            
        self.open_main_window(role_id, role_name, full_name, user_id)

    def login_as_guest(self):
        self.open_main_window(None, "Гость", "Гость", None)

    def open_main_window(self, role_id, role_name, full_name, user_id=None):
        from main import MainWindow
        self.main_window = MainWindow(self.db, role_id, role_name, full_name, user_id)
        self.main_window.show()
        self.close()