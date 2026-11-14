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

router = Router()


# Стани для FSM
class OrderState(StatesGroup):
  waiting_for_screenshot = State()


class SupportState(StatesGroup):
  waiting_for_message = State()


# База даних у пам'яті для профілю
user_profiles = {}


def get_profile(user_id: int):
  if user_id not in user_profiles:
    user_profiles[user_id] = {
        "stars_bought": 0,
        "prem_bought": 0,
        "reg_date": "Сьогодні",
    }
  return user_profiles[user_id]


# --- Головне меню (Кнопки знизу) ---
def main_menu():
  return types.ReplyKeyboardMarkup(
      keyboard=[
          [
              types.KeyboardButton(text="⭐ Telegram Stars"),
              types.KeyboardButton(text="💎 Telegram Premium"),
          ],
          [
              types.KeyboardButton(text="👤 Профіль"),
              types.KeyboardButton(text="🛠 Підтримка"),
          ],
          [types.KeyboardButton(text="💬 Відгуки")],
      ],
      resize_keyboard=True,
  )


# --- Кнопка "Назад" ---
def back_button():
  return InlineKeyboardMarkup(
      inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")]]
  )


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  get_profile(message.from_user.id)
  await message.answer(
      "Вітаємо в StarlyStars ⭐. Що бажаєте придбати?", reply_markup=main_menu()
  )


# Кнопка Відгуки
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


# --- Каталог Telegram Stars (повний з картинки) ---
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
  await state.update_data(item=f"{count} зірок ({price} грн)")
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


@router.callback_query(F.data == "custom_stars")
async def custom_stars_info(callback: types.CallbackQuery):
  await callback.message.edit_text(
      "Для придбання своєї кількості зірок, напишіть власнику магазину @Mk_Bars",
      reply_markup=back_button(),
  )
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
  await state.update_data(item=f"Premium {period} ({price} грн)")
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


# --- Профіль ---
@router.message(F.text == "👤 Профіль")
async def profile_handler(message: types.Message):
  p = get_profile(message.from_user.id)
  text = (
      f"👤 **Ваш профіль:**\n\n"
      f"🆔 Номер акаунту (ID): `{message.from_user.id}`\n"
      f"📅 Дата створення: {p['reg_date']}\n"
      f"⭐ Всього придбано зірок: {p['stars_bought']}\n"
      f"💎 Всього придбано Premium: {p['prem_bought']}"
  )
  await message.answer(text, parse_mode="Markdown")


# --- Підтримка ---
@router.message(F.text == "🛠 Підтримка")
async def support_handler(message: types.Message, state: FSMContext):
  await state.set_state(SupportState.waiting_for_message)
  await message.answer(
      "Напишіть будь ласка вашу проблему, адміністрація зв'яжеться з вами якомога скоріше.",
      reply_markup=back_button(),
  )


@router.message(SupportState.waiting_for_message)
async def send_support_to_admin(message: types.Message, state: FSMContext, bot: Bot):
  user_name = message.from_user.full_name
  user_id = message.from_user.id
  text = (
      f"📩 **Нове звернення у підтримку!**\n\n"
      f"Від: {user_name} (ID: `{user_id}`)\n"
      f"Повідомлення: {message.text}"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💬 Відповісти користувачу", url=f"tg://user?id={user_id}"
              )
          ]
      ]
  )
  await bot.send_message(ADMIN_ID, text, reply_markup=kb, parse_mode="Markdown")
  await state.clear()
  await message.answer("Ваше повідомлення надіслано адміністрації!", reply_markup=main_menu())


# --- Обробка скріншота оплати ---
@router.message(OrderState.waiting_for_screenshot, F.photo)
async def receive_screenshot(message: types.Message, state: FSMContext, bot: Bot):
  data = await state.get_data()
  item = data.get("item", "Товар")
  user_id = message.from_user.id
  user_name = message.from_user.full_name

  photo_id = message.photo[-1].file_id

  admin_caption = (
      f"💰 **Нова оплата!**\n\n"
      f"Користувач: {user_name} (ID: `{user_id}`)\n"
      f"Товар: {item}"
  )
  admin_kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="✅ Успішно", callback_data=f"approve_{user_id}"
              ),
              InlineKeyboardButton(
                  text="❌ Відхилено", callback_data=f"decline_{user_id}"
              ),
          ]
      ]
  )

  await bot.send_photo(
      ADMIN_ID, photo=photo_id, caption=admin_caption, reply_markup=admin_kb, parse_mode="Markdown"
  )
  await state.clear()
  await message.answer(
      "Почекайте поки триває перевірка оплати, це займає близько 5-60 хв",
      reply_markup=main_menu(),
  )


# --- Адмін управління (Успішно / Відхилено) ---
@router.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: types.CallbackQuery, bot: Bot):
  user_id = int(callback.data.split("_")[1])
  await bot.send_message(
      user_id, "✅ Ваша оплата успішна! Зірки/Преміум скоро будуть нараховані."
  )
  await callback.message.edit_caption(
      caption=callback.message.caption
      + "\n\n**[СТАТУС: ОПЛАТУ СХВАЛЕНО ✅]**",
      parse_mode="Markdown",
  )
  await callback.answer("Ви схвалили оплату!")


@router.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: types.CallbackQuery, bot: Bot):
  user_id = int(callback.data.split("_")[1])
  await bot.send_message(
      user_id, "❌ Вашу оплату було відхилено. Зверніться в підтримку."
  )
  await callback.message.edit_caption(
      caption=callback.message.caption
      + "\n\n**[СТАТУС: ОПЛАТУ ВІДХИЛЕНО ❌]**",
      parse_mode="Markdown",
  )
  await callback.answer("Ви відхилили оплату.")


# Повернення в головне меню
@router.callback_query(F.data == "back_home")
async def back_home_cb(callback: types.CallbackQuery, state: FSMContext):
  await state.clear()
  await callback.message.answer("Головне меню:", reply_markup=main_menu())
  try:
    await callback.message.delete()
  except Exception:
    pass
  await callback.answer()


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO, stream=sys.stdout)
  asyncio.run(main())
