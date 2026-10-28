import psycopg2
from psycopg2 import pool

class Database:
    def __init__(self):
        try:
            self.pool = pool.SimpleConnectionPool(
                1, 5, host="localhost", port=5432,
                database="mir_jurnalov", user="postgres", password="123" 
            )
        except psycopg2.Error:
            self.pool = None

    def get_conn(self):
        return self.pool.getconn() if self.pool else None

    def put_conn(self, conn):
        if self.pool: self.pool.putconn(conn)

    def check_login(self, login):
        conn = self.get_conn()
        if not conn: return None
        cur = conn.cursor()
        cur.execute("""
            SELECT u.user_id, u.role_id, u.last_name, u.first_name, u.middle_name, r.name 
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.login = %s
        """, (login,))
        res = cur.fetchone()
        cur.close()
        self.put_conn(conn)
        return res

    def get_catalog(self):
        conn = self.get_conn()
        if not conn: return []
        cur = conn.cursor()
        cur.execute("""
            SELECT m.model_id, m.name, c.name, p.name, m.base_price, m.image_path,
                   COALESCE(SUM(s.quantity), 0) AS total_qty
            FROM models m
            LEFT JOIN categories c ON m.category_id = c.category_id
            LEFT JOIN publishers p ON m.publisher_id = p.publisher_id
            LEFT JOIN stock_items s ON m.model_id = s.model_id
            GROUP BY m.model_id, c.name, p.name
        """)
        res = cur.fetchall()
        cur.close()
        self.put_conn(conn)
        return res

    def get_categories(self):
        conn = self.get_conn()
        if not conn: return []
        cur = conn.cursor()
        cur.execute("SELECT name FROM categories ORDER BY name")
        res = [row[0] for row in cur.fetchall()]
        cur.close()
        self.put_conn(conn)
        return res

    def get_model_details(self, model_id):
        conn = self.get_conn()
        if not conn: return None
        cur = conn.cursor()
        cur.execute("""
            SELECT m.name, c.name, p.name, m.base_price, m.description, m.composition, m.image_path
            FROM models m
            LEFT JOIN categories c ON m.category_id = c.category_id
            LEFT JOIN publishers p ON m.publisher_id = p.publisher_id
            WHERE m.model_id = %s
        """, (model_id,))
        res = cur.fetchone()
        cur.close()
        self.put_conn(conn)
        return res

    def get_variants(self, model_id):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.stock_item_id, v.variant_name, s.price, s.quantity
            FROM stock_items s
            JOIN variants v ON s.variant_id = v.variant_id
            WHERE s.model_id = %s AND s.quantity > 0
        """, (model_id,))
        res = cur.fetchall()
        cur.close()
        self.put_conn(conn)
        return res

    def get_all_orders(self):
        conn = self.get_conn()
        if not conn: return []
        cur = conn.cursor()
        cur.execute("""
            SELECT o.order_id, o.order_date, u.last_name, u.first_name, u.middle_name,
                   COALESCE(SUM(oi.quantity * oi.price), 0) AS total_sum
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id, u.last_name, u.first_name, u.middle_name
            ORDER BY o.order_id DESC
        """)
        res = cur.fetchall()
        cur.close()
        self.put_conn(conn)
        return res

    def get_order_details(self, order_id):
        conn = self.get_conn()
        if not conn: return []
        cur = conn.cursor()
        cur.execute("""
            SELECT oi.order_item_id, m.name, p.name, v.variant_name, oi.quantity, oi.price, (oi.quantity * oi.price) as total
            FROM order_items oi
            JOIN stock_items s ON oi.stock_item_id = s.stock_item_id
            JOIN models m ON s.model_id = m.model_id
            JOIN publishers p ON m.publisher_id = p.publisher_id
            JOIN variants v ON s.variant_id = v.variant_id
            WHERE oi.order_id = %s
        """, (order_id,))
        res = cur.fetchall()
        cur.close()
        self.put_conn(conn)
        return res

    def create_order(self, user_id, cart_items):
        conn = self.get_conn()
        if not conn: return False
        cur = conn.cursor()
        try:
            for item in cart_items:
                stock_id, qty = item
                cur.execute("SELECT quantity FROM stock_items WHERE stock_item_id = %s", (stock_id,))
                current_qty = cur.fetchone()[0]
                if current_qty < qty:
                    return False
            
            cur.execute("INSERT INTO orders (user_id) VALUES (%s) RETURNING order_id", (user_id,))
            order_id = cur.fetchone()[0]
            
            for item in cart_items:
                stock_id, qty = item
                cur.execute("SELECT price FROM stock_items WHERE stock_item_id = %s", (stock_id,))
                price = cur.fetchone()[0]
                cur.execute("INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (%s, %s, %s, %s)", 
                            (order_id, stock_id, qty, price))
                cur.execute("UPDATE stock_items SET quantity = quantity - %s WHERE stock_item_id = %s", (qty, stock_id))
                
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            self.put_conn(conn)

    def delete_order(self, order_id):
        conn = self.get_conn()
        if not conn: return False
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE stock_items s
                SET quantity = s.quantity + oi.quantity
                FROM order_items oi
                WHERE s.stock_item_id = oi.stock_item_id AND oi.order_id = %s
            """, (order_id,))
            cur.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()
            self.put_conn(conn)

    def delete_order_item(self, order_item_id):
        conn = self.get_conn()
        if not conn: return False
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE stock_items s
                SET quantity = s.quantity + oi.quantity
                FROM order_items oi
                WHERE s.stock_item_id = oi.stock_item_id AND oi.order_item_id = %s
            """, (order_item_id,))
            cur.execute("DELETE FROM order_items WHERE order_item_id = %s", (order_item_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()
            self.put_conn(conn)

    def update_order_date(self, order_id, new_date):
        conn = self.get_conn()
        if not conn: return False
        cur = conn.cursor()
        try:
            cur.execute("UPDATE orders SET order_date = %s WHERE order_id = %s", (new_date, order_id))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()
            self.put_conn(conn)

    def get_all_clients(self):
        conn = self.get_conn()
        if not conn: return []
        cur = conn.cursor()
        cur.execute("SELECT user_id, last_name, first_name, middle_name FROM users WHERE role_id = 3")
        res = cur.fetchall()
        cur.close()
        self.put_conn(conn)
        return res

    def get_all_stock_items(self):
        conn = self.get_conn()
        if not conn: return []
        cur = conn.cursor()
        cur.execute("""
            SELECT s.stock_item_id, m.name, s.price, s.quantity
            FROM stock_items s
            JOIN models m ON s.model_id = m.model_id
            WHERE s.quantity > 0
        """)
        res = cur.fetchall()
        cur.close()
        self.put_conn(conn)
        return res
