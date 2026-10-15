# -*- coding: utf-8 -*-
"""
Telegram-бот — віртуальний помічник психотерапевтки Юлії Жаркової.

Що вміє:
  • /start — вітальне фото, привітання та меню з кнопок;
  • «🌷 Хочу на сесію» — запис у 3 кроки (формат -> зручний час -> заявка адміністратору) на FSM;
  • «💡 Інформація», «🛠 Послуги», «🗓 Графік роботи», «📝 Інформ. згода» — довідкові тексти;
  • «↗️ Instagram» — кнопка-посилання.

Запуск:
pip3 install -r requirements.txt
export BOT_TOKEN="ваш_токен_от_BotFather"
export ADMIN_ID="ваш_Telegram_ID"
python bot.py

Бот працює на aiogram v3, Python 3.10+.
"""

import asyncio
import html
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, CallbackQuery, FSInputFile, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ======================================================================
# НАЛАШТУВАННЯ — замініть значення-заглушки (або задайте змінні середовища)
# ======================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")                    # токен від @BotFather
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))                # Telegram ID, куди надходять заявки
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://instagram.com/zhara_j")
TELEGRAM_CONTACT = "https://t.me/fox_joy"
FACEBOOK_URL = "https://www.facebook.com/profile.php?id=100001833233456"
WAPP_PROFILE_URL = "https://wapp.member365.org/sharingnetwork/myProfile#profile_personal"
WAPP_CERTIFICATE_URL = "https://wapp.member365.org/mms/api/viewMembershipTemplate/b2AR9ssUYrirGD83CrMxKeV6o0wPBLBN"
CONTACT_EMAIL = "zyulia@yahoo.com"
CONTACT_PHONE = "+380953545050"

WELCOME_PHOTO = Path(__file__).with_name("welcome.jpg")   # вітальне фото (лежить поруч із bot.py)

CITY = "Київ"            # використовується в запитанні про очний формат: «Очний у м. …»
CITY_GEN = "Києва"       # те саме у родовому відмінку: «у центрі …»

# Підтверджені тарифи: індивідуальна консультація — 35€, пакет із 4 сесій — 120€.
PRICE_CONSULTATION = "35€"
PRICE_PACKAGE = "120€"

# Години прийому. Якщо залишити порожнім — рядок із годинами у «Графіку роботи» не показується.
# Приклад: WORKING_HOURS = ""
WORKING_HOURS = ""

# ======================================================================
# ТЕКСТИ
# ======================================================================
WELCOME_CAPTION = (
    "Вітаю! 🌿 Я — помічник психотерапевтки Юлії Жаркової. Допоможу записатися на індивідуальну "
    "сесію (60 хвилин) або сесію для пари (90 хвилин). Напиши, який формат і час тобі зручні."
)

BOOKING_STEP1 = (
    f"🛋 Індивідуальна консультація триває 60 хвилин, вартість {PRICE_CONSULTATION}.\n\n"
    f"✉️ Пакет із 4 сесій — {PRICE_PACKAGE}. Періодичність сесій узгоджується індивідуально.\n\n"
    "Який формат для вас буде найзручнішим?"
)

BOOKING_STEP2 = (
    f"Супер! Напиши, який формат сесії тобі зручний: Очний у м. {CITY} або онлайн? "
    "Які дні та часи тобі зручні для сесії? Психолог перевірить свій графік та ви узгодите "
    "комфортну для вас сесію."
)

BOOKING_DONE = (
    "Дякую! 🌷 Твій запит успішно надіслано. Психолог перегляне свій графік і зв’яжеться з тобою "
    "найближчим часом, щоб узгодити сесію."
)

BOOKING_ERROR = (
    "На жаль, не вдалося надіслати запит. Спробуй, будь ласка, ще раз за кілька хвилин "
    "або напиши психологу напряму."
)

BOOKING_NEED_TEXT = "Будь ласка, напиши відповідь текстом ✍️ Щоб вийти із запису, натисни /cancel."

FALLBACK_TEXT = (
    "Дякую, що написав(-ла) 🌿 Щоб записатися на сесію, натисни «🌷 Хочу на сесію» — "
    "я передам запит психологу. Усю інформацію можна знайти в меню нижче.\n\n"
    "Якщо ти зараз у небезпеці або в гострій кризі — зателефонуй за номером 112."
)

INFO_TEXT = (
    "<b>💡 Інформація</b>\n\n"
    "<b>Юлія Жаркова</b> — сертифікована психотерапевтка у методі Позитивної психотерапії "
    "(Certificate No. UKR-597-2025), Магістр психології. Живе й працює в Києві понад 20 років.\n\n"
    "• Закінчила Майстер-курс Українського Інституту Позитивної Психотерапії та є дійсною членкинею WAPP.\n"
    "• Метод Позитивної психотерапії, заснований Н. Пезешкіаном, спирається на те, що в людині вже є, "
    "і розглядає життя в чотирьох сферах — тіло, діяльність, контакти та сенси.\n"
    "• Працює із тривогою, пригніченим настроєм, кризами, втратою сенсів, труднощами у стосунках, "
    "самооцінкою, почуттям провини й сорому та пошуком внутрішньої опори.\n"
    "• Працює з підлітками й дорослими та з повагою ставиться до різноманіття сексуальних орієнтацій "
    "і гендерних ідентичностей.\n"
    "• Регулярно проходить супервізію та дотримується професійної етики.\n\n"
    "Психотерапія — це спільне дослідження того, що відбувається у житті, почуттів і потреб, "
    "зв’язку теперішніх труднощів із минулим досвідом та пошук нових способів розв’язання проблем. "
    "Не оцінюю й не нав’язую готових рішень. Разом ми створимо простір, де можна відкрито говорити про важливе, "
    "бути почутими та поступово знаходити відповіді. Регулярно проходжу супервізії й дотримуюся професійних етичних принципів.\n\n"
    f"<a href=\"{WAPP_PROFILE_URL}\">Профіль WAPP</a> · "
    f"<a href=\"{WAPP_CERTIFICATE_URL}\">Членський сертифікат WAPP (English)</a>\n\n"
    f"<b>Контакти:</b> {CONTACT_EMAIL} · {CONTACT_PHONE}"
)

SERVICES_TEXT = (
    "<b>🛠 Послуги</b>\n\n"
    f"🛋 <b>Індивідуальна консультація</b> — 60 хвилин, {PRICE_CONSULTATION}.\n"
    "👫 <b>Консультація для пари</b> — 90 хвилин.\n"
    f"✉️ <b>Пакет із 4 сесій</b> — {PRICE_PACKAGE}.\n\n"
    "<b>З чим можна прийти:</b> тривога, депресивні переживання, криза сенсів, труднощі у внутрішньому, сімейному, "
    "робочому та соціальному житті.\n\n"
    "<b>Формат:</b> онлайн через зручний для клієнта засіб зв’язку або очно в кабінеті "
    f"в центрі {CITY_GEN}. Індивідуальна сесія — 60 хвилин, для пари — 90 хвилин. "
    "Кількість та періодичність сесій узгоджуються індивідуально."
)

SCHEDULE_TEXT = (
    "<b>🗓 Графік роботи</b>\n\n"
    "Сесії проводяться за попереднім записом: індивідуальна — 60 хвилин, для пари — 90 хвилин. "
    "Періодичність узгоджується індивідуально. Дні й години психолог узгоджує — натисни «🌷 Хочу на сесію» "
    "і напиши, коли тобі зручно."
    + (f"\n\n<b>Години прийому:</b> {html.escape(WORKING_HOURS)}" if WORKING_HOURS else "")
    + "\n\nСкасувати або перенести сесію можна не пізніше ніж за 24 години "
    "(правило діє з другої сесії)."
)

# Текст контракту (формується з файлу контракту; банківські реквізити з нього прибрано)
CONTRACT_ITEMS = [
    [
        "Індивідуальна психотерапевтична сесія триває 60 хвилин, сесія для пари — 90 хвилин. Мова роботи узгоджується індивідуально.",
        []
    ],
    [
        "Кількість і періодичність сесій узгоджуються індивідуально. Після сесії можливе надання домашнього завдання.",
        []
    ],
    [
        "Вартість однієї консультації — 35 євро (або гривневий еквівалент).",
        []
    ],
    [
        "Оплата здійснюється протягом 24 годин після завершення консультації. Реквізити для оплати (картка для України, PayPal для інших країн) надсилаються після підтвердження запису.",
        []
    ],
    [
        "Будь-які зміни (оплата, час, формат роботи, спосіб контакту) обговорюються заздалегідь та узгоджуються обома сторонами.",
        []
    ],
    [
        "Психотерапевт використовує свій професійний та життєвий досвід для досягнення позитивного результату психотерапевтичної роботи.",
        []
    ],
    [
        "Клієнт має право отримувати інформацію про методи роботи психотерапевта, його освіту та професійний досвід.",
        []
    ],
    [
        "На період дії контракту не допускається зміна соціальних ролей між клієнтом і психотерапевтом, зокрема вступ у дружні, сімейні або ділові відносини.",
        []
    ],
    [
        "Уся інформація, надана клієнтом, є строго конфіденційною і не передається третім особам. Винятком є супервізія, під час якої особисті дані клієнта не розкриваються.",
        []
    ],
    [
        "Клієнт має право зупиняти будь-які звернення, запитання або пропозиції, які викликають дискомфорт. Уся інформація в терапії є важливою та має сенс.",
        []
    ],
    [
        "На час сесії обидві сторони зобов’язуються забезпечити належні умови для роботи: уважність, по можливості — перебування наодинці.",
        []
    ],
    [
        "Заборонено перебувати на сесії у стані алкогольного сп’яніння або під впливом речовин, що змінюють свідомість (наркотичні, заспокійливі), якщо вони не призначені лікарем для постійного приймання. Психотерапевтична робота у зміненому стані свідомості є небезпечною.",
        []
    ],
    [
        "Усе, що відбувається під час консультації — від вітання до завершення — є частиною психологічної роботи.",
        []
    ],
    [
        "Саморозкриття сприяє прискоренню терапевтичного процесу. Ритм, темп і стиль роботи є індивідуальними.",
        []
    ],
    [
        "У разі бажання завершити терапевтичні відносини клієнт повідомляє про це за одну сесію. Завершення є важливою фазою терапії та розглядається як можливість змінити способи взаємодії із собою та з іншими.",
        []
    ],
    [
        "Після завершення етапу психотерапії можливе переконтрактування за бажанням клієнта.",
        []
    ],
    [
        "Психотерапевт може вести нотатки під час сесії, фіксуючи важливі моменти. Клієнт самостійно вирішує доцільність власних записів.",
        []
    ],
    [
        "Правила сеттінгу починають діяти з другої сесії:",
        [
            "скасування або перенесення можливе не пізніше ніж за 24 години;",
            "у разі запізнення психотерапевта втрачені хвилини компенсуються."
        ]
    ],
    [
        "У разі форс-мажорних обставин (воєнні дії, відсутність світла чи інтернету, стихійні лиха) можливі інші домовленості.",
        []
    ],
    [
        "У разі хвороби рекомендується повідомляти заздалегідь. Турбота про власне здоров’я є важливою.",
        []
    ],
    [
        "Договір може бути змінений або доповнений за взаємною згодою сторін.",
        []
    ],
    [
        "Онлайн-робота (Telegram / Viber / Skype / WhatsApp) за правилами та відповідальністю не відрізняється від очної психотерапії.",
        []
    ]
]
CONTRACT_FINAL = "Контракт набирає чинності після ознайомлення та усної згоди клієнта."

# ======================================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ======================================================================
def split_message(text: str, limit: int = 3800) -> list[str]:
    """Ділить довгий текст на частини за абзацами (ліміт Telegram — 4096 символів)."""
    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = block
    if current:
        chunks.append(current)
    return chunks


def build_consent_messages() -> list[str]:
    lines = ["<b>📝 Психотерапевтичний контракт (інформована згода)</b>", ""]
    for number, (text, subitems) in enumerate(CONTRACT_ITEMS, start=1):
        lines.append(f"{number}. {html.escape(text)}")
        for sub in subitems:
            lines.append(f"      – {html.escape(sub)}")
        lines.append("")
    lines.append(f"<i>{html.escape(CONTRACT_FINAL)}</i>")
    return split_message("\n".join(lines))


CONSENT_MESSAGES = build_consent_messages()

FORMATS = {
    "consultation": f"Консультація (60 хв, {PRICE_CONSULTATION})",
    "package": f"Пакет (4 сесії, {PRICE_PACKAGE})",
    "couple": "Консультація для пари (90 хв)",
}

# ======================================================================
# КЛАВІАТУРИ
# ======================================================================
def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌷 Хочу на сесію", callback_data="menu:book")
    kb.button(text="💡 Інформація", callback_data="menu:info")
    kb.button(text="🛠 Послуги", callback_data="menu:services")
    kb.button(text="🗓 Графік роботи", callback_data="menu:schedule")
    kb.button(text="📝 Інформ. згода", callback_data="menu:consent")
    kb.button(text="↗️ Instagram", url=INSTAGRAM_URL)
    kb.button(text="👤 Telegram @fox_joy", url=TELEGRAM_CONTACT)
    kb.button(text="📘 Facebook", url=FACEBOOK_URL)
    kb.button(text="📄 Профіль WAPP", url=WAPP_PROFILE_URL)
    kb.adjust(1)
    return kb.as_markup()


def format_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Консультація", callback_data="fmt:consultation")
    kb.button(text="Для пари · 90 хв", callback_data="fmt:couple")
    kb.button(text="Пакет", callback_data="fmt:package")
    kb.button(text="↩️ Меню", callback_data="menu:home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


# ======================================================================
# FSM
# ======================================================================
class Booking(StatesGroup):
    waiting_details = State()   # чекаємо повідомлення про зручний формат і час


router = Router()
_welcome_file_id: str | None = None   # кеш file_id, щоб не вантажити фото щоразу


async def send_to_user(call: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    """Надсилає нове повідомлення в чат користувача (вітання — це фото, тож редагувати його не можна)."""
    await call.bot.send_message(call.from_user.id, text, reply_markup=reply_markup)


# ----------------------------------------------------------------------
# /start, /menu, /cancel
# ----------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    global _welcome_file_id
    await state.clear()
    try:
        photo = _welcome_file_id or FSInputFile(WELCOME_PHOTO)
        sent = await message.answer_photo(photo, caption=WELCOME_CAPTION, reply_markup=main_menu())
        if not _welcome_file_id and sent.photo:
            _welcome_file_id = sent.photo[-1].file_id
    except (FileNotFoundError, TelegramAPIError):
        logging.exception("Не вдалося надіслати вітальне фото — надсилаю лише текст")
        await message.answer(WELCOME_CAPTION, reply_markup=main_menu())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Обери, що тебе цікавить:", reply_markup=main_menu())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    had_state = await state.get_state() is not None
    await state.clear()
    text = "Запис скасовано. Ти завжди можеш почати знову 🌿" if had_state else "Зараз немає активних дій."
    await message.answer(text, reply_markup=main_menu())


# ----------------------------------------------------------------------
# Меню: інформаційні розділи
# ----------------------------------------------------------------------
@router.callback_query(F.data == "menu:home")
async def cb_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await send_to_user(call, "Обери, що тебе цікавить:", main_menu())
    await call.answer()


@router.callback_query(F.data.in_({"menu:info", "menu:services", "menu:schedule", "menu:consent"}))
async def cb_sections(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    section = call.data.split(":", 1)[1]

    if section == "consent":
        for i, chunk in enumerate(CONSENT_MESSAGES):
            is_last = i == len(CONSENT_MESSAGES) - 1
            await send_to_user(call, chunk, main_menu() if is_last else None)
    else:
        texts = {"info": INFO_TEXT, "services": SERVICES_TEXT, "schedule": SCHEDULE_TEXT}
        await send_to_user(call, texts[section], main_menu())
    await call.answer()


# ----------------------------------------------------------------------
# Запис на сесію: крок 1 -> крок 2 -> крок 3 (FSM)
# ----------------------------------------------------------------------
@router.callback_query(F.data == "menu:book")
async def cb_book(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await send_to_user(call, BOOKING_STEP1, format_menu())          # крок 1: вибір формату
    await call.answer()


@router.callback_query(F.data.startswith("fmt:"))
async def cb_format(call: CallbackQuery, state: FSMContext) -> None:
    label = FORMATS.get(call.data.split(":", 1)[1])
    if label is None:
        await call.answer("Невідомий формат, спробуй ще раз.", show_alert=True)
        return
    await state.set_state(Booking.waiting_details)                    # крок 2: чекаємо деталі
    await state.update_data(format=label)
    await send_to_user(call, BOOKING_STEP2)
    await call.answer()


@router.message(Booking.waiting_details, F.text, ~F.text.startswith("/"))
async def booking_details(message: Message, state: FSMContext, bot: Bot) -> None:
    """Крок 3: надсилаємо заявку адміністратору (психотерапевтці)."""
    data = await state.get_data()
    user = message.from_user

    full_name = html.escape(user.full_name or "—")
    username = f"@{html.escape(user.username)}" if user.username else "—"
    request_text = html.escape(message.text[:3000])

    admin_text = (
        "🆕 <b>Нова заявка на сесію</b>\n\n"
        f"<b>Формат:</b> {html.escape(data.get('format', '—'))}\n"
        f"<b>Клієнт:</b> {full_name}\n"
        f"<b>Username:</b> {username}\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f'<b>Чат:</b> <a href="tg://user?id={user.id}">відкрити профіль</a>\n\n'
        f"<b>Повідомлення клієнта:</b>\n{request_text}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except TelegramAPIError:
        logging.exception("Не вдалося надіслати заявку адміністратору (ADMIN_ID=%s)", ADMIN_ID)
        await message.answer(BOOKING_ERROR)      # стан не скидаємо — можна повторити
        return

    await state.clear()
    await message.answer(BOOKING_DONE, reply_markup=main_menu())


@router.message(Booking.waiting_details)
async def booking_non_text(message: Message) -> None:
    await message.answer(BOOKING_NEED_TEXT)


# ----------------------------------------------------------------------
# Будь-які інші повідомлення (має бути зареєстровано останнім)
# ----------------------------------------------------------------------
@router.message()
async def fallback(message: Message) -> None:
    await message.answer(FALLBACK_TEXT, reply_markup=main_menu())


# ======================================================================
# ЗАПУСК
# ======================================================================
async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not BOT_TOKEN:
        raise SystemExit("Вкажіть BOT_TOKEN (змінна середовища або значення в bot.py).")
    if not ADMIN_ID:
        raise SystemExit("Вкажіть ADMIN_ID — Telegram ID, на який надходитимуть заявки.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Почати спочатку"),
        BotCommand(command="menu", description="Показати меню"),
        BotCommand(command="cancel", description="Скасувати запис"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущено")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
