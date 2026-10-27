import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QScrollArea, 
                               QMessageBox, QLineEdit, QDialog, QComboBox, QTableWidget, QTableWidgetItem)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from database import Database
from login_window import LoginWindow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCE_PATH = os.path.join(BASE_DIR, "resources")

class VariantDialog(QDialog):
    def __init__(self, db, model_id, model_name, role_id):
        super().__init__()
        self.setWindowTitle(f"Выпуски: {model_name}")
        self.resize(400, 300)
        self.setStyleSheet("font-family: Calibri; background-color: #FFFFFF;")
        self.role_id = role_id
        self.selected_item = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Выберите доступный выпуск:</b>"))
        
        variants = db.get_variants(model_id)
        if not variants:
            layout.addWidget(QLabel("Нет в наличии"))
        
        for var in variants:
            stock_id, var_name, price, qty = var
            btn = QPushButton(f"{var_name} — {price:.2f} ₽ (Остаток: {qty} экз.)")
            btn.setStyleSheet("""
                QPushButton { background-color: #D2F6E7; color: #000000; 
                              padding: 10px; border-radius: 5px; text-align: left; }
                QPushButton:hover { background-color: #70B2AF; }
            """)
            if self.role_id is None:
                btn.setEnabled(False)
                btn.setText(f"{var_name} — {price:.2f} ₽ (Войдите для заказа)")
                
            btn.clicked.connect(lambda checked, s=stock_id, v=var_name, p=price, q=qty: self.select_item(s, v, p, q))
            layout.addWidget(btn)

    def select_item(self, stock_id, var_name, price, qty):
        self.selected_item = (stock_id, var_name, price, qty)
        self.accept()

class DetailsDialog(QDialog):
    def __init__(self, db, model_id):
        super().__init__()
        self.setWindowTitle("Подробная информация")
        self.resize(600, 400)
        self.setStyleSheet("font-family: Calibri; background-color: #FFFFFF;")
        
        details = db.get_model_details(model_id)
        if not details:
            QMessageBox.warning(self, "Ошибка", "Информация не найдена")
            self.close()
            return
            
        name, cat, pub, base_price, desc, comp, img_path = details
        
        layout = QHBoxLayout(self)
        
        img_label = QLabel()
        img_label.setFixedSize(200, 280)
        img_label.setAlignment(Qt.AlignCenter)
        
        pix = QPixmap()
        if img_path:
            real_img = os.path.join(RESOURCE_PATH, img_path)
            if os.path.exists(real_img):
                pix = QPixmap(real_img)
        if pix.isNull():
            fallback = os.path.join(RESOURCE_PATH, "picture.png")
            if os.path.exists(fallback):
                pix = QPixmap(fallback)
                
        if not pix.isNull():
            img_label.setPixmap(pix.scaled(200, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(img_label)
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel(f"<h2>{name}</h2>"))
        text_layout.addWidget(QLabel(f"<b>Издатель:</b> {pub}"))
        text_layout.addWidget(QLabel(f"<b>Категория:</b> {cat}"))
        text_layout.addWidget(QLabel(f"<b>Цена:</b> от {float(base_price):.2f} ₽"))
        
        text_layout.addWidget(QLabel("<b>Описание:</b>"))
        desc_label = QLabel(desc if desc else "Описание отсутствует")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        text_layout.addWidget(QLabel("<b>Состав:</b>"))
        comp_label = QLabel(comp if comp else "Состав не указан")
        comp_label.setWordWrap(True)
        text_layout.addWidget(comp_label)
        
        text_layout.addStretch()
        layout.addLayout(text_layout)

class CartDialog(QDialog):
    def __init__(self, db, user_id, cart_items):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.cart_items = cart_items
        
        self.setWindowTitle("Корзина")
        self.resize(500, 400)
        self.setStyleSheet("font-family: Calibri; background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Ваш заказ:</h2>"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.list_layout = QVBoxLayout(self.scroll_widget)
        
        total = 0
        for item in self.cart_items:
            stock_id, name, price, qty = item
            total += float(price) * 1 
            row = QLabel(f"{name} — {price} ₽ x 1 шт.")
            self.list_layout.addWidget(row)
            
        self.scroll.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll)
        
        layout.addWidget(QLabel(f"<h3>Итого к оплате: {total:.2f} ₽</h3>"))
        
        self.btn_confirm = QPushButton("Подтвердить заказ")
        self.btn_confirm.setStyleSheet("background-color: #70B2AF; color: black; font-weight: bold; padding: 10px; font-size: 16px;")
        self.btn_confirm.clicked.connect(self.confirm_order)
        layout.addWidget(self.btn_confirm)

    def confirm_order(self):
        order_list = [(item[0], 1) for item in self.cart_items]
        
        if self.user_id is None:
            QMessageBox.warning(self, "Ошибка", "Гости не могут оформлять заказы!")
            return
            
        success = self.db.create_order(self.user_id, order_list)
        
        if success:
            QMessageBox.information(self, "Успех", "Заказ успешно оформлен! Остатки обновлены.")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось оформить заказ. Возможно, товара не хватает на складе.")

class OrdersListDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Управление заказами (Все заказы)")
        self.resize(700, 500)
        self.setStyleSheet("font-family: Calibri; background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Список всех заказов</h2>"))
        
        self.table = QTableWidget()
        orders = db.get_all_orders()
        self.table.setRowCount(len(orders))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["№ Заказа", "Дата", "ФИО Клиента", "Сумма (₽)", "Статус"])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        for row_idx, order in enumerate(orders):
            o_id, o_date, l_name, f_name, m_name, total_sum = order
            
            fio = f"{l_name} {f_name}"
            if m_name: fio += f" {m_name}"
            
            date_str = o_date.strftime("%d.%m.%Y") if o_date else ""
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(o_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(date_str))
            self.table.setItem(row_idx, 2, QTableWidgetItem(fio))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{float(total_sum):.2f}"))
            self.table.setItem(row_idx, 4, QTableWidgetItem("Выполнен"))
            
        layout.addWidget(self.table)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class MainWindow(QMainWindow):
    def __init__(self, db, role_id=None, role_name="Гость", full_name="Гость", user_id=None):
        super().__init__()
        self.db = db
        self.role_id = role_id
        self.role_name = role_name
        self.full_name = full_name
        self.user_id = user_id
        self.cart = []
        
        self.setWindowTitle("Мир журналов - Каталог")
        self.resize(1000, 800)
        
        icon_path = os.path.join(RESOURCE_PATH, "Мир журналов.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet("""
            QMainWindow { background-color: #FFFFFF; font-family: Calibri; }
            QLabel { color: #000000; font-size: 14px; }
            QPushButton.main-btn { background-color: #70B2AF; color: #000000; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton.admin-btn { background-color: #D2F6E7; color: #000000; font-weight: bold; padding: 8px; border-radius: 4px; }
            QLineEdit, QComboBox { font-size: 14px; padding: 5px; border: 1px solid #ccc; }
        """)
        
        self.setup_ui()
        self.load_catalog()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header = QHBoxLayout()
        logo = QLabel()
        
        logo_path = os.path.join(RESOURCE_PATH, "Мир журналов.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            logo.setPixmap(pix.scaledToWidth(200))
        else:
            logo.setText("Логотип не найден")
            
        header.addWidget(logo)
        header.addStretch()
        
        user_info = QLabel(f"{self.full_name} ({self.role_name})")
        user_info.setStyleSheet("font-weight: bold; font-size: 16px;")
        header.addWidget(user_info)
        
        if self.role_id is not None:
            self.btn_cart = QPushButton("Корзина (0)")
            self.btn_cart.clicked.connect(self.open_cart)
            header.addWidget(self.btn_cart)
        
        btn_logout = QPushButton("Выход")
        btn_logout.clicked.connect(self.logout)
        header.addWidget(btn_logout)
        main_layout.addLayout(header)

        admin_panel = QHBoxLayout()
        self.btn_orders = QPushButton("Управление заказами")
        self.btn_orders.setProperty("class", "admin-btn")
        self.btn_orders.clicked.connect(lambda: OrdersListDialog(self.db).exec())
        
        if self.role_id in [1, 2]:
            admin_panel.addWidget(self.btn_orders)
            main_layout.addLayout(admin_panel)

        if self.role_id is not None:
            filter_layout = QHBoxLayout()
            
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Поиск по названию...")
            self.search_input.textChanged.connect(self.load_catalog)
            filter_layout.addWidget(self.search_input)
            
            self.category_combo = QComboBox()
            self.category_combo.addItem("Все категории")
            
            categories = self.db.get_categories()
            for cat in categories:
                self.category_combo.addItem(cat)
                
            self.category_combo.currentIndexChanged.connect(self.load_catalog)
            filter_layout.addWidget(self.category_combo)
            
            main_layout.addLayout(filter_layout)
        else:
            self.search_input = QLineEdit()
            self.search_input.hide()
            self.category_combo = QComboBox()
            self.category_combo.hide()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.list_layout = QVBoxLayout(self.scroll_widget)
        self.scroll.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll)

    def load_catalog(self):
        for i in reversed(range(self.list_layout.count())): 
            self.list_layout.itemAt(i).widget().setParent(None)

        search_text = self.search_input.text().lower() if self.role_id is not None else ""
        selected_category = self.category_combo.currentText() if self.role_id is not None else "Все категории"

        for item in self.db.get_catalog():
            m_id, name, cat, pub, base_price, img_path, total_qty, avail_variants = item
            
            if search_text not in name.lower():
                continue
                
            if selected_category != "Все категории" and cat != selected_category:
                continue
                
            self.list_layout.addWidget(self.create_card(m_id, name, cat, pub, base_price, img_path, total_qty, avail_variants))

    def create_card(self, m_id, name, cat, pub, base_price, img_path, total_qty, avail_variants):
        card = QWidget()
        card.setLayout(QHBoxLayout())
        
        if total_qty <= 3:
            card.setStyleSheet("background-color: #ff8080; border: 1px solid #ccc; margin-bottom: 5px; border-radius: 5px;")
        else:
            card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc; margin-bottom: 5px; border-radius: 5px;")

        layout = card.layout()

        img_label = QLabel()
        img_label.setFixedSize(120, 160)
        img_label.setStyleSheet("border: none;")
        img_label.setAlignment(Qt.AlignCenter)
        
        pix = QPixmap()
        if img_path:
            real_image_path = os.path.join(RESOURCE_PATH, img_path)
            if os.path.exists(real_image_path):
                pix = QPixmap(real_image_path)
                
        if pix.isNull():
            fallback_path = os.path.join(RESOURCE_PATH, "picture.png")
            if os.path.exists(fallback_path):
                pix = QPixmap(fallback_path)
                
        if not pix.isNull():
            img_label.setPixmap(pix.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText("Нет фото")
                
        layout.addWidget(img_label)

        info_layout = QVBoxLayout()
        
        name_label = QLabel(f"<b><u>{name}</u></b>")
        name_label.setStyleSheet("color: #000000; font-size: 16px; cursor: pointer;")
        name_label.mousePressEvent = lambda event: DetailsDialog(self.db, m_id).exec()
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(QLabel(f"Издатель: {pub}"))
        info_layout.addWidget(QLabel(f"Категория: {cat}"))
        
        info_layout.addWidget(QLabel(f"Доступно выпусков: {avail_variants}"))
        
        qty_text = f"Всего экз.: {total_qty}" if total_qty > 0 else "Недоступно для заказа"
        qty_label = QLabel(qty_text)
        if total_qty == 0: qty_label.setStyleSheet("color: red; font-weight: bold;")
        info_layout.addWidget(qty_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()

        action_layout = QVBoxLayout()
        base_price_float = float(base_price) 
        discount_percent = 15 if total_qty < 10 else 0
        new_price = base_price_float * (1 - discount_percent / 100)
        
        action_layout.addWidget(QLabel("Цена:"))
        
        if discount_percent > 0:
            old_price_label = QLabel(f"<s>{base_price_float:.2f} ₽</s>")
            old_price_label.setStyleSheet("color: red; font-size: 13px;")
            action_layout.addWidget(old_price_label)
            
            new_price_label = QLabel(f"{new_price:.2f} ₽")
            new_price_label.setStyleSheet("color: black; font-weight: bold; font-size: 16px;")
            action_layout.addWidget(new_price_label)
        else:
            price_label = QLabel(f"от {base_price_float:.2f} ₽")
            price_label.setStyleSheet("color: black; font-weight: bold; font-size: 16px;")
            action_layout.addWidget(price_label)
            
        btn = QPushButton("Выбрать выпуск")
        btn.setProperty("class", "main-btn")
        btn.clicked.connect(self.open_variant_dialog_wrapper(m_id, name))
        
        if self.role_id is None:
            btn.setEnabled(False)
            btn.setText("Войдите для заказа")
            
        action_layout.addWidget(btn)
        layout.addLayout(action_layout)

        return card

    def open_variant_dialog_wrapper(self, m_id, name):
        def open_dialog():
            dialog = VariantDialog(self.db, m_id, name, self.role_id)
            if dialog.exec() == QDialog.Accepted and dialog.selected_item:
                self.cart.append(dialog.selected_item)
                self.btn_cart.setText(f"Корзина ({len(self.cart)})")
                QMessageBox.information(self, "Успех", "Товар добавлен в корзину!")
        return open_dialog

    def open_cart(self):
        if not self.cart:
            QMessageBox.information(self, "Корзина", "Ваша корзина пуста.")
            return
            
        cart_dialog = CartDialog(self.db, self.user_id, self.cart)
        if cart_dialog.exec() == QDialog.Accepted:
            self.cart.clear()
            self.btn_cart.setText("Корзина (0)")
            self.load_catalog()

    def logout(self):
        self.login_window = LoginWindow(self.db)
        self.login_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication([])
    db = Database()
    window = LoginWindow(db)
    window.show()
    app.exec()