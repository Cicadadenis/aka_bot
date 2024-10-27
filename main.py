import sqlite3
from telethon import TelegramClient, events

# Данные для подключения
api_id = 1325339
api_hash = "b826075fd7ea762e6b9f853146d47995"

# Изначальный ID администратора
main_admin_id = 1144785510  # Ваш основной Telegram ID

# Инициализация бота

# Инициализация бота
bot = TelegramClient('anon', api_id, api_hash)
bot.start()# Ваш основной Telegram ID

# Подключение к базе данных SQLite
conn = sqlite3.connect("bot_data.db")
cursor = conn.cursor()

# Создание таблиц для хранения ссылок и администраторов
cursor.execute('''CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link TEXT
                  )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY
                  )''')

# Добавление основного администратора в базу данных
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (main_admin_id,))
conn.commit()

# Функция для получения списка администраторов
def get_admin_ids():
    cursor.execute("SELECT user_id FROM admins")
    return {row[0] for row in cursor.fetchall()}

# Флаг для индикации состояния админ-меню
admin_mode = False

# Хранилище одноразовых ссылок и индикатор их использования
available_links = []  # Список доступных ссылок
issued_links = {}     # Словарь для хранения выданных ссылок пользователям

# Реакция на любое текстовое сообщение для выдачи одноразовой ссылки
@bot.on(events.NewMessage)
async def on_message(event):
    global admin_mode
    user_id = event.sender_id

    # Игнорируем команды, если администратор в режиме админ-меню
    if user_id in get_admin_ids() and admin_mode:
        return

    # Проверка, выдавалась ли ссылка
    if user_id in issued_links:
        await event.reply("Вы уже получили одноразовую ссылку.")
    elif available_links:
        # Выдаем следующую ссылку и помечаем её как использованную
        link = available_links.pop(0)
        issued_links[user_id] = link
        await event.reply(f"Ваша одноразовая ссылка: {link}")
    else:
        await event.reply("Извините, но в данный момент нет доступных ссылок.")

# Команда /admin для доступа к админ-меню
@bot.on(events.NewMessage(pattern='/admin'))
async def admin(event):
    global admin_mode
    if event.sender_id not in get_admin_ids():
        await event.reply("У вас нет прав для выполнения этой команды.")
        return

    # Активируем режим админ-меню
    admin_mode = True
    admin_text = (
        f"Админ-меню:\n"
        f"<code>/setlinks</code> <ссылки через пробел> — Установить новые ссылки пачкой\n"
        f"<code>/showlinks</code> — Показать все доступные ссылки\n"
        f"<code>/add</code> <ID> — Добавить нового администратора\n"
        f"<code>/showadmins</code> — Показать всех администраторов\n"
        f"<code>/clear</code> — Очистить список ссылок\n"
        f"<code>/exit</code> — Выйти из админ-меню"
    )
    await event.reply(admin_text)

# Команда /exitadmin для выхода из админ-меню
@bot.on(events.NewMessage(pattern='/exit'))
async def exit_admin(event):
    global admin_mode
    if event.sender_id not in get_admin_ids():
        await event.reply("У вас нет прав для выполнения этой команды.")
        return

    # Отключаем режим админ-меню
    admin_mode = False
    await event.reply("Вы вышли из админ-меню.")

# Команда /setlinks для добавления пачки ссылок
@bot.on(events.NewMessage(pattern='/setlinks'))
async def set_links(event):
    global admin_mode
    if event.sender_id not in get_admin_ids() or not admin_mode:
        await event.reply("У вас нет прав для выполнения этой команды.")
        return

    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        await event.reply("Пожалуйста, укажите ссылки через пробел.")
        return

    new_links = args[1].split()
    
    # Добавляем новые ссылки в базу данных и список
    cursor.executemany("INSERT INTO links (link) VALUES (?)", [(link,) for link in new_links])
    conn.commit()
    available_links.extend(new_links)  # Обновляем общий список
    await event.reply(f"Добавлено {len(new_links)} новых ссылок.")
    # Команда /showlinks для отображения всех доступных ссылок
@bot.on(events.NewMessage(pattern='/showlinks'))
async def show_links(event):
    global admin_mode
    if event.sender_id not in get_admin_ids() or not admin_mode:
        await event.reply("У вас нет прав для выполнения этой команды.")
        return

    # Получаем все доступные ссылки
    cursor.execute("SELECT link FROM links")
    rows = cursor.fetchall()
    if rows:
        await event.reply("Доступные ссылки:\n" + "\n".join([row[0] for row in rows]))
    else:
        await event.reply("В данный момент нет доступных ссылок.")

# Команда /addadmin для добавления нового администратора
@bot.on(events.NewMessage(pattern='/add'))
async def add_admin(event):
    global admin_mode
    if event.sender_id != main_admin_id or not admin_mode:
        await event.reply("Только главный администратор может добавлять новых администраторов.")
        return

    args = event.message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await event.reply("Пожалуйста, укажите ID нового администратора.")
        return

    new_admin_id = int(args[1])
    
    # Добавляем нового администратора в базу данных
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
    conn.commit()
    await event.reply(f"Пользователь с ID {new_admin_id} добавлен в список администраторов.")

# Команда /showadmins для отображения всех администраторов
@bot.on(events.NewMessage(pattern='/showadmins'))
async def show_admins(event):
    global admin_mode
    if event.sender_id not in get_admin_ids() or not admin_mode:
        await event.reply("У вас нет прав для выполнения этой команды.")
        return

    cursor.execute("SELECT user_id FROM admins")
    rows = cursor.fetchall()
    if rows:
        await event.reply("Администраторы:\n" + "\n".join([str(row[0]) for row in rows]))
    else:
        await event.reply("В данный момент нет администраторов.")

# Команда /clearlinks для очистки списка ссылок
@bot.on(events.NewMessage(pattern='/clear'))
async def clear_links(event):
    global admin_mode
    if event.sender_id not in get_admin_ids() or not admin_mode:
        await event.reply("У вас нет прав для выполнения этой команды.")
        return

    # Очищаем список ссылок в базе данных и в памяти
    cursor.execute("DELETE FROM links")
    conn.commit()
    available_links.clear()  # Очищаем список ссылок в памяти
    await event.reply("Список ссылок очищен.")

# Запуск бота
print("Бот запущен...")
bot.run_until_disconnected()

# Закрытие соединения с базой данных при завершении работы
conn.close()
