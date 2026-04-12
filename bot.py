import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from contract_service import generate_contract
from db_service import (
    save_contract,
    get_last_contracts,
    get_contract_by_id,
    update_contract_status,
    get_contracts_by_status,
    get_contract_file_by_id,
)

load_dotenv()

TOKEN = os.getenv("TOKEN")
EXPERT_CHAT_ID = int(os.getenv("EXPERT_CHAT_ID", "0"))


FIELDS_ORDER = [
    ("CLIENT_FIO", "Введите ФИО клиента:"),
    ("REG_ADDRESS", "Введите адрес регистрации клиента:"),
    ("PHONE", "Введите номер телефона клиента:"),
    ("PASSPORT", "Введите паспорт (серия и номер):"),
    ("PASSPORT_ISSUED_BY", "Введите кем выдан паспорт (как в паспорте):"),
    ("PASSPORT_ISSUED_DATE", "Введите дату выдачи паспорта (ДД.ММ.ГГГГ):"),
    ("AUTO_MODEL", "Введите марку и модель автомобиля:"),
    ("AUTO_YEAR", "Введите год выпуска автомобиля (например 2016):"),
    ("VIN", "Введите VIN (17 символов):"),
    ("GOS_NUMBER", "Введите госномер:"),
    ("STS_NUMBER", "Введите номер СТС (свидетельство о регистрации ТС):"),
    ("CITY", "Введите город:"),
    ("DATE", "Введите дату договора (ДД.ММ.ГГГГ) или '-' чтобы поставить сегодняшнюю:"),
]

FIELD_TITLES = {
    "CLIENT_FIO": "ФИО",
    "REG_ADDRESS": "Адрес регистрации",
    "PHONE": "Телефон",
    "PASSPORT": "Паспорт",
    "PASSPORT_ISSUED_BY": "Кем выдан паспорт",
    "PASSPORT_ISSUED_DATE": "Дата выдачи паспорта",
    "AUTO_MODEL": "Марка и модель автомобиля",
    "AUTO_YEAR": "Год выпуска",
    "VIN": "VIN",
    "GOS_NUMBER": "Госномер",
    "STS_NUMBER": "СТС",
    "CITY": "Город",
    "DATE": "Дата договора",
}


def is_expert(user_id: int) -> bool:
    return user_id == EXPERT_CHAT_ID


def is_valid_date_format(value: str) -> bool:
    if len(value) != 10:
        return False
    if value[2] != "." or value[5] != ".":
        return False

    day = value[:2]
    month = value[3:5]
    year = value[6:]

    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return False

    d = int(day)
    m = int(month)
    y = int(year)

    if y < 2000 or y > 2100:
        return False
    if m < 1 or m > 12:
        return False
    if d < 1 or d > 31:
        return False

    return True


def validate_input(field_key: str, value: str):
    v = value.strip()

    if field_key == "CLIENT_FIO":
        parts = [part for part in v.split() if part]
        if len(parts) < 2:
            return "Введите ФИО более полно. Пример: Иванов Иван Иванович."
        if len(v) < 8:
            return "ФИО слишком короткое."

    if field_key == "REG_ADDRESS":
        if len(v) < 8:
            return "Адрес слишком короткий. Введите адрес регистрации полностью."

    if field_key == "PHONE":
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10 or len(digits) > 12:
            return "Телефон введён некорректно. Пример: +79991234567."

    if field_key == "PASSPORT":
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            return "Паспорт введён некорректно. Пример: 1234 567890."

    if field_key == "PASSPORT_ISSUED_BY":
        if len(v) < 5:
            return "Слишком коротко. Введите 'кем выдан' как в паспорте."

    if field_key == "PASSPORT_ISSUED_DATE":
        if not is_valid_date_format(v):
            return "Дата выдачи должна быть в формате ДД.ММ.ГГГГ."

    if field_key == "AUTO_MODEL":
        if len(v) < 2:
            return "Введите марку и модель автомобиля."

    if field_key == "AUTO_YEAR":
        if not v.isdigit() or len(v) != 4:
            return "Год выпуска должен быть 4 цифры. Пример: 2016."
        year = int(v)
        if year < 1950 or year > 2035:
            return "Введите реальный год выпуска."

    if field_key == "VIN":
        if len(v) != 17:
            return "VIN должен содержать ровно 17 символов."

    if field_key == "GOS_NUMBER":
        if len(v) < 5:
            return "Госномер слишком короткий."
        if len(v) > 9:
            return "Госномер слишком длинный (не более 9 символов)."

    if field_key == "STS_NUMBER":
        if len(v) < 6:
            return "Номер СТС слишком короткий."

    if field_key == "CITY":
        if len(v) < 2:
            return "Введите город."

    if field_key == "DATE":
        if v == "-":
            return None
        if not is_valid_date_format(v):
            return "Дата договора должна быть в формате ДД.ММ.ГГГГ или '-'"

    return None


def build_summary_text(data: dict) -> str:
    return (
        "Проверьте введённые данные:\n\n"
        f"ФИО: {data.get('CLIENT_FIO', '')}\n"
        f"Адрес регистрации: {data.get('REG_ADDRESS', '')}\n"
        f"Телефон: {data.get('PHONE', '')}\n"
        f"Паспорт: {data.get('PASSPORT', '')}\n"
        f"Кем выдан: {data.get('PASSPORT_ISSUED_BY', '')}\n"
        f"Дата выдачи паспорта: {data.get('PASSPORT_ISSUED_DATE', '')}\n"
        f"Автомобиль: {data.get('AUTO_MODEL', '')}\n"
        f"Год выпуска: {data.get('AUTO_YEAR', '')}\n"
        f"VIN: {data.get('VIN', '')}\n"
        f"Госномер: {data.get('GOS_NUMBER', '')}\n"
        f"СТС: {data.get('STS_NUMBER', '')}\n"
        f"Город: {data.get('CITY', '')}\n"
        f"Дата договора: {data.get('DATE', '') or 'сегодняшняя дата'}"
    )


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton("✏️ Исправить данные", callback_data="confirm_edit")],
        [InlineKeyboardButton("🔄 Заполнить заново", callback_data="confirm_restart")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_edit_fields_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("ФИО", callback_data="edit_field:CLIENT_FIO"),
            InlineKeyboardButton("Телефон", callback_data="edit_field:PHONE"),
        ],
        [
            InlineKeyboardButton("Адрес", callback_data="edit_field:REG_ADDRESS"),
            InlineKeyboardButton("Паспорт", callback_data="edit_field:PASSPORT"),
        ],
        [
            InlineKeyboardButton("Кем выдан", callback_data="edit_field:PASSPORT_ISSUED_BY"),
            InlineKeyboardButton("Дата выдачи", callback_data="edit_field:PASSPORT_ISSUED_DATE"),
        ],
        [
            InlineKeyboardButton("Авто", callback_data="edit_field:AUTO_MODEL"),
            InlineKeyboardButton("Год", callback_data="edit_field:AUTO_YEAR"),
        ],
        [
            InlineKeyboardButton("VIN", callback_data="edit_field:VIN"),
            InlineKeyboardButton("Госномер", callback_data="edit_field:GOS_NUMBER"),
        ],
        [
            InlineKeyboardButton("СТС", callback_data="edit_field:STS_NUMBER"),
            InlineKeyboardButton("Город", callback_data="edit_field:CITY"),
        ],
        [
            InlineKeyboardButton("Дата договора", callback_data="edit_field:DATE"),
        ],
        [
            InlineKeyboardButton("⬅ Назад к сводке", callback_data="edit_back"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_summary(update_or_query_message, context: ContextTypes.DEFAULT_TYPE):
    data_for_doc = {k: context.user_data.get(k, "") for k, _ in FIELDS_ORDER}
    summary_text = build_summary_text(data_for_doc)
    context.user_data["confirm_stage"] = True
    await update_or_query_message.reply_text(
        summary_text,
        reply_markup=build_confirm_keyboard(),
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш chat_id: {update.effective_user.id}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("📝 Заполнить договор", callback_data="fill_contract")],
        [InlineKeyboardButton("🔄 Сброс", callback_data="reset")],
    ]

    if is_expert(user_id):
        await update.message.reply_text(
            "Здравствуйте! Вы вошли как эксперт.\n\n"
            "Доступные команды:\n"
            "/history — последние заявки\n"
            "/get 5 — открыть заявку по ID\n"
            "/status 5 done — изменить статус\n"
            "/file 5 — получить договор по ID\n\n"
            "Также можно заполнить договор вручную:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            "Здравствуйте! Я бот для заполнения договора автоэксперта.\n"
            "Нажмите «Заполнить договор» и ответьте на вопросы.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_expert(user_id):
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    allowed_statuses = ["new", "in_progress", "done", "canceled"]

    if context.args:
        status = context.args[0].lower()

        if status not in allowed_statuses:
            await update.message.reply_text(
                "Используй: /history new | in_progress | done | canceled"
            )
            return

        contracts = await get_contracts_by_status(status)

        if not contracts:
            await update.message.reply_text("Нет заявок с таким статусом.")
            return

        text = f"Заявки со статусом {status}:\n\n"
    else:
        contracts = await get_last_contracts(5)

        if not contracts:
            await update.message.reply_text("Заявок пока нет.")
            return

        text = "Последние заявки:\n\n"

    for c in contracts:
        text += (
            f"ID: {c.id}\n"
            f"ФИО: {c.client_fio}\n"
            f"Телефон: {c.phone}\n"
            f"Авто: {c.auto_model}\n"
            f"VIN: {c.vin}\n"
            f"Статус: {c.status}\n\n"
        )

    await update.message.reply_text(text)


async def get_contract_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_expert(user_id):
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /get 5")
        return

    try:
        contract_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом. Пример: /get 5")
        return

    contract = await get_contract_by_id(contract_id)

    if not contract:
        await update.message.reply_text("Заявка с таким ID не найдена.")
        return

    text = (
        f"Заявка ID: {contract.id}\n\n"
        f"ФИО: {contract.client_fio}\n"
        f"Адрес: {contract.reg_address}\n"
        f"Телефон: {contract.phone}\n\n"
        f"Паспорт: {contract.passport}\n"
        f"Кем выдан: {contract.passport_issued_by}\n"
        f"Дата выдачи: {contract.passport_issued_date}\n\n"
        f"Авто: {contract.auto_model}\n"
        f"Год: {contract.auto_year}\n"
        f"VIN: {contract.vin}\n"
        f"Госномер: {contract.gos_number}\n"
        f"СТС: {contract.sts_number}\n\n"
        f"Город: {contract.city}\n"
        f"Дата договора: {contract.contract_date}\n\n"
        f"Статус: {contract.status}"
    )

    await update.message.reply_text(text)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_expert(user_id):
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /status 5 done\n"
            "Доступные статусы: new, in_progress, done, canceled"
        )
        return

    try:
        contract_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом. Пример: /status 5 done")
        return

    new_status = context.args[1].strip().lower()
    allowed_statuses = ["new", "in_progress", "done", "canceled"]

    if new_status not in allowed_statuses:
        await update.message.reply_text(
            "Недопустимый статус.\n"
            "Используй: new, in_progress, done, canceled"
        )
        return

    contract = await update_contract_status(contract_id, new_status)

    if not contract:
        await update.message.reply_text("Заявка с таким ID не найдена.")
        return

    await update.message.reply_text(
        f"Статус заявки {contract.id} изменён на: {contract.status}"
    )


async def file_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_expert(user_id):
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /file 5")
        return

    try:
        contract_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом. Пример: /file 5")
        return

    file_path = await get_contract_file_by_id(contract_id)

    if not file_path:
        await update.message.reply_text("Заявка с таким ID не найдена.")
        return

    if not os.path.exists(file_path):
        await update.message.reply_text("Файл по этой заявке не найден на диске.")
        return

    try:
        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                caption=f"Договор по заявке ID {contract_id}"
            )
    except Exception as e:
        await update.message.reply_text(f"Ошибка отправки файла: {e}")


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    if query.data == "fill_contract":
        context.user_data.clear()
        context.user_data["field_index"] = 0
        context.user_data["confirm_stage"] = False
        context.user_data["editing_field"] = None

        _, first_question = FIELDS_ORDER[0]
        await query.message.reply_text(first_question)
        return

    if query.data == "reset":
        context.user_data.clear()
        await query.message.reply_text("Сбросил данные ✅ Нажмите /start.")
        return

    if query.data == "confirm_edit":
        context.user_data["confirm_stage"] = False
        await query.message.reply_text(
            "Выберите поле, которое хотите исправить:",
            reply_markup=build_edit_fields_keyboard(),
        )
        return

    if query.data == "edit_back":
        await send_summary(query.message, context)
        return

    if query.data.startswith("edit_field:"):
        field_key = query.data.split(":", 1)[1]
        context.user_data["editing_field"] = field_key
        context.user_data["confirm_stage"] = False

        question = None
        for key, q in FIELDS_ORDER:
            if key == field_key:
                question = q
                break

        title = FIELD_TITLES.get(field_key, field_key)
        await query.message.reply_text(
            f"Исправление поля: {title}\n\n{question}"
        )
        return

    if query.data == "confirm_yes":
        data_for_doc = {k: context.user_data.get(k, "") for k, _ in FIELDS_ORDER}

        await query.message.reply_text("Формирую договор...")

        try:
            file_path = generate_contract(data_for_doc)
            await query.message.reply_text("Договор создан ✅")
        except Exception as e:
            await query.message.reply_text(
                "Ошибка при создании договора.\n"
                f"Ошибка: {e}"
            )
            context.user_data.clear()
            return

        try:
            contract_id = await save_contract(data_for_doc, file_path)
            await query.message.reply_text(f"Сохранено в базе ✅ ID: {contract_id}")
        except Exception as e:
            await query.message.reply_text(f"Ошибка сохранения в базе: {e}")
            context.user_data.clear()
            return

        if EXPERT_CHAT_ID:
            try:
                with open(file_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=EXPERT_CHAT_ID,
                        document=f,
                        caption=f"Новая заявка ✅\nID в базе: {contract_id}\nСтатус: new"
                    )
                await query.message.reply_text("Спасибо! Договор отправлен эксперту ✅")
            except Exception as e:
                await query.message.reply_text(f"Ошибка отправки эксперту: {e}")
        else:
            await query.message.reply_text("EXPERT_CHAT_ID не задан ❌")

        context.user_data.clear()
        return

    if query.data == "confirm_restart":
        context.user_data.clear()
        context.user_data["field_index"] = 0
        context.user_data["confirm_stage"] = False
        context.user_data["editing_field"] = None

        _, first_question = FIELDS_ORDER[0]
        await query.message.reply_text("Хорошо, начинаем заново.\n" + first_question)
        return


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    editing_field = context.user_data.get("editing_field")

    if editing_field:
        text = update.message.text.strip()

        error = validate_input(editing_field, text)
        if error:
            await update.message.reply_text(error)
            await update.message.reply_text("Введите ещё раз:")
            return

        if editing_field == "DATE" and text == "-":
            text = ""

        context.user_data[editing_field] = text
        context.user_data["editing_field"] = None

        await update.message.reply_text("Поле обновлено ✅")
        await send_summary(update.message, context)
        return

    if context.user_data.get("confirm_stage"):
        await update.message.reply_text(
            "Сейчас нужно нажать кнопку: ✅ Подтвердить, ✏️ Исправить данные или 🔄 Заполнить заново."
        )
        return

    if "field_index" not in context.user_data:
        await update.message.reply_text("Нажмите /start и кнопку «📝 Заполнить договор».")
        return

    idx = context.user_data["field_index"]

    if idx < 0 or idx >= len(FIELDS_ORDER):
        context.user_data.clear()
        await update.message.reply_text("Ошибка состояния. Нажмите /start и начните заново.")
        return

    field_key, _ = FIELDS_ORDER[idx]
    text = update.message.text.strip()

    error = validate_input(field_key, text)
    if error:
        await update.message.reply_text(error)
        await update.message.reply_text("Введите ещё раз:")
        return

    if field_key == "DATE" and text == "-":
        text = ""

    context.user_data[field_key] = text

    idx += 1
    context.user_data["field_index"] = idx

    if idx >= len(FIELDS_ORDER):
        await send_summary(update.message, context)
        return

    _, next_question = FIELDS_ORDER[idx]
    await update.message.reply_text(next_question)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("get", get_contract_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("file", file_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()