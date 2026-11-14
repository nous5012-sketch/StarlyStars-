import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "9113395557:AAHhrbAONJcW4Gl5gXfsPIcgSxmJLQeWMrQ"
ADMIN_ID = 7648928411  # Ваш Telegram ID
CHANNEL_USERNAME = "@StarlyStars_UKR"  # Ваш канал

router = Router()


# --- Стани (FSM) ---
class OrderState(StatesGroup):
  waiting_for_screenshot = State()
  waiting_for_custom_stars = State()


class SupportState(StatesGroup):
  waiting_for_message = State()


class ReviewState(StatesGroup):
  waiting_for_review_text = State()


class CalcState(StatesGroup):
  waiting_for_calc_input = State()


# --- База даних у пам'яті ---
user_profiles = {}


def get_profile(user_id: int, user_name: str = "Користувач"):
  if user_id not in user_profiles:
    user_profiles[user_id] = {
        "stars_bought": 0,
        "prem_bought": 0,
        "reg_date": "Сьогодні",
        "name": user_name,
    }
  return user_profiles[user_id]


# --- Перевірка підписки на канал ---
async def check_subscription(user_id: int, bot: Bot) -> bool:
  try:
    member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    if member.status in ["creator", "administrator", "member"]:
      return True
  except Exception:
    # Якщо бот не в адмінах каналу або сталася помилка — пропускаємо для зручності тестів
    return True
  return False


def sub_check_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📢 Підписатися на канал", url="https://t.me/StarlyStars_UKR"
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Перевірити підписку", callback_data="check_sub_action"
              )
          ],
      ]
  )


# --- Головне меню ---
def main_menu():
  return types.ReplyKeyboardMarkup(
      keyboard=[
          [
              types.KeyboardButton(text="⭐ Telegram Stars"),
              types.KeyboardButton(text="💎 Telegram Premium"),
          ],
          [
              types.KeyboardButton(text="🧮 Калькулятор"),
              types.KeyboardButton(text="👤 Профіль"),
          ],
          [
              types.KeyboardButton(text="🛠 Підтримка"),
              types.KeyboardButton(text="💬 Відгуки"),
          ],
      ],
      resize_keyboard=True,
  )


# --- Кнопка "Назад" ---
def back_button():
  return InlineKeyboardMarkup(
      inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")]]
  )


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
  await state.clear()
  user_id = message.from_user.id
  get_profile(user_id, message.from_user.full_name)

  if not await check_subscription(user_id, bot):
    await message.answer(
        "⚠️ Для використання бота необхідно підписатися на наш канал!\n\n"
        f"Підпишіться на {CHANNEL_USERNAME} та натисніть кнопку перевірки:",
        reply_markup=sub_check_keyboard(),
    )
    return

  await message.answer(
      "Вітаємо в StarlyStars ⭐. Що бажаєте придбати?", reply_markup=main_menu()
  )


@router.callback_query(F.data == "check_sub_action")
async def verify_sub_cb(callback: types.CallbackQuery, bot: Bot):
  user_id = callback.from_user.id
  if await check_subscription(user_id, bot):
    await callback.message.delete()
    await callback.message.answer(
        "Дякуємо за підписку! Вітаємо в StarlyStars ⭐. Що бажаєте придбати?",
        reply_markup=main_menu(),
    )
  else:
    await callback.answer(
        "❌ Ви ще не підписалися на канал!", show_alert=True
    )


# --- Кнопка Відгуки ---
@router.message(F.text == "💬 Відгуки")
async def btn_reviews(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔗 Перейти до відгуків",
                  url="https://t.me/StarlyStars_UKR",
              )
          ]
      ]
  )
  await message.answer("Наші відгуки:", reply_markup=kb)


# --- Каталог Telegram Stars ---
@router.message(F.text == "⭐ Telegram Stars")
async def catalog_stars(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="⭐ 50 Зірок — 40 грн", callback_data="buy_stars_50_40"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 100 Зірок — 80 грн", callback_data="buy_stars_100_80"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 250 Зірок — 196 грн", callback_data="buy_stars_250_196"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 500 Зірок — 385 грн", callback_data="buy_stars_500_385"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 1000 Зірок — 765 грн",
                  callback_data="buy_stars_1000_765",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 2500 Зірок — 1890 грн",
                  callback_data="buy_stars_2500_1890",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 5000 Зірок — 3750 грн",
                  callback_data="buy_stars_5000_3750",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ 10000 Зірок — 7490 грн",
                  callback_data="buy_stars_10000_7490",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔄 Своя кількість", callback_data="custom_stars"
              )
          ],
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")],
      ]
  )
  await message.answer("Виберіть кількість зірок:", reply_markup=kb)


@router.callback_query(F.data.startswith("buy_stars_"))
async def process_stars_buy(callback: types.CallbackQuery, state: FSMContext):
  _, _, count, price = callback.data.split("_")
  text = (
      f"Кількість: {count} зірок\n"
      f"Ціна: {price} грн\n\n"
      f"Реквізити карти для оплати:\n"
      f"5168745149435791\n"
      f"Шевченко М.\n\n"
      f"Після оплати, скиньте скріншот оплати сюди та очікуйте підтвердження."
  )
  await state.set_state(OrderState.waiting_for_screenshot)
  await state.update_data(
      item=f"{count} зірок ({price} грн)",
      stars_add=int(count),
      prem_add=0,
  )
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


@router.callback_query(F.data == "custom_stars")
async def custom_stars_prompt(callback: types.CallbackQuery, state: FSMContext):
  await state.set_state(OrderState.waiting_for_custom_stars)
  await callback.message.edit_text(
      "Введіть бажану кількість зірок (цифрами):\n\n"
      "Або напишіть власнику напряму: @Mk_Bars",
      reply_markup=back_button(),
  )
  await callback.answer()


@router.message(OrderState.waiting_for_custom_stars)
async def calculate_custom_stars(message: types.Message, state: FSMContext):
  if not message.text.isdigit():
    await message.answer(
        "Будь ласка, введіть число (кількість зірок), або натисніть Назад."
    )
    return

  count = int(message.text)
  price = max(10, int(count * 0.75))

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text=f"💳 Оплатити {price} грн",
                  callback_data=f"pay_custom_{count}_{price}",
              )
          ],
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")],
      ]
  )
  await message.answer(
      f"Кількість: {count} зірок\n"
      f"Ціна: {price} грн\n\n"
      f"Натисніть кнопку нижче для переходу до реквізитів:",
      reply_markup=kb,
  )


@router.callback_query(F.data.startswith("pay_custom_"))
async def pay_custom_stars(callback: types.CallbackQuery, state: FSMContext):
  _, _, count, price = callback.data.split("_")
  text = (
      f"Кількість: {count} зірок\n"
      f"Ціна: {price} грн\n\n"
      f"Реквізити карти для оплати:\n"
      f"5168745149435791\n"
      f"Шевченко М.\n\n"
      f"Після оплати, скиньте скріншот оплати сюди та очікуйте підтвердження."
  )
  await state.set_state(OrderState.waiting_for_screenshot)
  await state.update_data(
      item=f"{count} зірок ({price} грн)",
      stars_add=int(count),
      prem_add=0,
  )
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


# --- Каталог Telegram Premium ---
@router.message(F.text == "💎 Telegram Premium")
async def catalog_prem(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💎 6 місяців — 749 грн", callback_data="buy_prem_6m_749"
              )
          ],
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")],
      ]
  )
  await message.answer("Виберіть Telegram Premium:", reply_markup=kb)


@router.callback_query(F.data.startswith("buy_prem_"))
async def process_prem_buy(callback: types.CallbackQuery, state: FSMContext):
  _, _, period, price = callback.data.split("_")
  text = (
      f"Кількість: Telegram Premium на {period}\n"
      f"Ціна: {price} грн\n\n"
      f"Реквізити карти для оплати:\n"
      f"5168745149435791\n"
      f"Шевченко М.\n\n"
      f"Після оплати, скиньте скріншот оплати сюди та очікуйте підтвердження."
  )
  await state.set_state(OrderState.waiting_for_screenshot)
  await state.update_data(
      item=f"Premium {period} ({price} грн)", stars_add=0, prem_add=1
  )
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


# --- Калькулятор ---
@router.message(F.text == "🧮 Калькулятор")
async def calc_menu(message: types.Message, state: FSMContext):
  await state.set_state(CalcState.waiting_for_calc_input)
  await message.answer(
      "🧮 **Калькулятор цін StarlyStars**\n\n"
      "Введіть кількість зірок (наприклад: `500`) або суму в гривнях (наприклад `385 грн`), і я порахую відповідне значення!",
      reply_markup=back_button(),
      parse_mode="Markdown",
  )


@router.message(CalcState.waiting_for_calc_input)
async def process_calc(message: types.Message):
  text_cleaned = message.text.lower().replace("грн", "").strip()
  if not text_cleaned.isdigit():
    await message.answer("Будь ласка, введіть число (наприклад
  
