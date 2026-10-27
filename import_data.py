import pandas as pd
import psycopg2


conn = psycopg2.connect(
    host="localhost", port=5432, database="mir_jurnalov", 
    user="postgres", password="123"
)
cur = conn.cursor()

print("Очистка старых данных...")
cur.execute("TRUNCATE order_items, orders, stock_items, models, users, variants, publishers, categories, roles RESTART IDENTITY CASCADE;")

roles = [('Администратор',), ('Менеджер',), ('Авторизованный пользователь',)]
cur.executemany("INSERT INTO roles (name) VALUES (%s)", roles)

df_users = pd.read_excel('docs-import/Users_import.xlsx')
for _, row in df_users.iterrows():
    cur.execute("SELECT role_id FROM roles WHERE name = %s", (row['Роль'],))
    role_id = cur.fetchone()[0]
    cur.execute("""
        INSERT INTO users (last_name, first_name, middle_name, login, role_id) 
        VALUES (%s, %s, %s, %s, %s)
    """, (row['Фамилия'], row['Имя'], row['Отчество'], row['Логин'], role_id))

df_products = pd.read_excel('docs-import/Products_import.xlsx')
for cat in df_products['Категория'].unique():
    cur.execute("INSERT INTO categories (name) VALUES (%s)", (cat,))

for pub in df_products['Производство'].unique():
    cur.execute("INSERT INTO publishers (name) VALUES (%s)", (pub,))

variants = ['№ 1 за 2026 год', '№ 2 за 2026 год', '№ 3 за 2026 год']
for var in variants:
    cur.execute("INSERT INTO variants (variant_name) VALUES (%s)", (var,))

for _, row in df_products.iterrows():
    cur.execute("SELECT category_id FROM categories WHERE name = %s", (row['Категория'],))
    cat_id = cur.fetchone()[0]
    cur.execute("SELECT publisher_id FROM publishers WHERE name = %s", (row['Производство'],))
    pub_id = cur.fetchone()[0]
    
  
    img = row['Изображение'] if pd.notna(row['Изображение']) else None
    desc = row['Описание'] if pd.notna(row['Описание']) else None
    comp = row['Состав'] if pd.notna(row['Состав']) else None
    
    cur.execute("""
        INSERT INTO models (name, category_id, publisher_id, image_path, base_price, description, composition) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (row['Наименование товара'], cat_id, pub_id, img, row['Цена'], desc, comp))


df_stock = pd.read_excel('docs-import/Stock_Items_import.xlsx')
for _, row in df_stock.iterrows():
    cur.execute("""
        SELECT m.model_id FROM models m 
        JOIN publishers p ON m.publisher_id = p.publisher_id 
        WHERE m.name = %s AND p.name = %s
    """, (row['Наименование товара'], row['Производство']))
    model_id = cur.fetchone()[0]
    
    cur.execute("SELECT variant_id FROM variants WHERE variant_name = %s", (row['Вариант исполнения'],))
    var_id = cur.fetchone()[0]
    
    cur.execute("""
        INSERT INTO stock_items (model_id, variant_id, quantity, price) 
        VALUES (%s, %s, %s, %s)
    """, (model_id, var_id, row['Количество доступное для заказа'], row['Цена варианта']))

conn.commit()
cur.close()
conn.close()
print("Данные успешно импортированы вместе с описаниями!")