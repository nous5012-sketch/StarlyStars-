import asyncio
from datetime import datetime
import logging
import sys
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "9113395557:AAHhrbAONJcW4Gl5gXfsPIcgSxmJLQeWMrQ"
ADMIN_ID = 7648928411
CHANNEL_USERNAME = "@StarlyStars_UKR"
BOT_USERNAME = "@Shop_StarlyStars_bot"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
router = Router()


class OrderState(StatesGroup):
  waiting_for_screenshot = State()


class SupportState(StatesGroup):
  waiting_for_message = State()


class ReviewState(StatesGroup):
  waiting_for_review_text = State()


class BroadcastState(StatesGroup):
  waiting_for_broadcast_text = State()


user_profiles = {}
all_users = set()
order_counter = 5
pending_orders = {}


def get_profile(user_id: int, user_name: str = "Користувач"):
  if user_id not in user_profiles:
    reg_date_str = datetime.now().strftime("%d.%m.%Y")
    user_profiles[user_id] = {
        "stars_bought": 0,
        "prem_bought": 0,
        "reg_date": reg_date_str,
        "name": user_name,
        "referred_count": 0,
        "referred_users": [],
        "ref_balance": 0.0,
        "purchase_history": [],
    }
  return user_profiles[user_id]


async def check_subscription(user_id: int, bot: Bot) -> bool:
  try:
    member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    return member.status in ["creator", "administrator", "member"]
  except Exception as e:
    logging.error(f"Помилка перевірки підписки: {e}")
    return False


def sub_check_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📢 Підписатися на канал",
                  url="https://t.me/StarlyStars_UKR",
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Перевірити підписку", callback_data="check_sub_action"
              )
          ],
      ]
  )


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


def profile_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📦 Історія покупок", callback_data="view_history"
              )
          ]
      ]
  )


def back_button():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")]
      ]
  )


@router.message(Command("start"))
async def cmd_start(
    message: types.Message, state: FSMContext, command: CommandObject, bot: Bot
):
  logging.info(f"Отримано /start від {message.from_user.id}")
  await state.clear()
  user_id = message.from_user.id
  user_name = message.from_user.full_name
  all_users.add(user_id)

  is_new_user = user_id not in user_profiles
  get_profile(user_id, user_name)

  args = command.args
  if args and args.startswith("ref") and is_new_user:
    try:
      referrer_id = int(args.replace("ref", ""))
      if referrer_id != user_id:
        ref_profile = get_profile(referrer_id)
        if user_id not in ref_profile["referred_users"]:
          ref_profile["referred_users"].append(user_id)
          ref_profile["referred_count"] += 0
          ref_profile["ref_balance"] += 0
          try:
            await bot.send_message(
                referrer_id,
                "🎉 За вашим реферальним посиланням зареєструвався новий"
                " користувач!",
            )
          except Exception:
            pass
    except Exception as e:
      logging.error(f"Помилка обробки реферала: {e}")

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


@router.message(Command("stats"))
async def admin_stats(message: types.Message):
  if message.from_user.id != ADMIN_ID:
    return

  total_users = len(all_users)
  total_orders = order_counter - 5
  total_stars = sum(p["stars_bought"] for p in user_profiles.values())
  total_prem = sum(p["prem_bought"] for p in user_profiles.values())

  stats_text = (
      "📊 Статистика бота StarlyStars:\n\n"
      f"👥 Всього користувачів: {total_users}\n"
      f"📦 Всього успішних замовлень: {total_orders}\n"
      f"⭐ Продано зірок: {total_stars}\n"
      f"💎 Продано Telegram Premium: {total_prem}"
  )

  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="📢 Зробити розсилку", callback_data="start_broadcast"
          )
      ]]
  )
  await message.answer(stats_text, reply_markup=kb)


@router.callback_query(F.data == "start_broadcast")
async def start_broadcast_cb(callback: types.CallbackQuery, state: FSMContext):
  if callback.from_user.id != ADMIN_ID:
    return
  await state.set_state(BroadcastState.waiting_for_broadcast_text)
  await callback.message.answer(
      "📢 Надішліть текст або картинку з текстом для розсилки всім користувачам"
      " бота:"
  )
  await callback.answer()


@router.message(BroadcastState.waiting_for_broadcast_text)
async def send_broadcast(message: types.Message, state: FSMContext):
  if message.from_user.id != ADMIN_ID:
    return
  await state.clear()
  await message.answer("⏳ Розсилка розпочалася...")

  success_count = 0
  fail_count = 0

  for uid in all_users:
    try:
      await message.send_copy(chat_id=uid)
      success_count += 1
      await asyncio.sleep(0.05)
    except Exception:
      fail_count += 1

  await message.answer(
      "✅ Розсилку завершено!\n\n"
      f"📤 Успішно доставлено: {success_count}\n"
      f"❌ Не вдалося доставити: {fail_count}"
  )


@router.callback_query(F.data == "check_sub_action")
async def verify_sub_cb(callback: types.CallbackQuery, bot: Bot):
  user_id = callback.from_user.id
  if await check_subscription(user_id, bot):
    try:
      await callback.message.delete()
    except Exception:
      pass
    await callback.message.answer(
        "Дякуємо за підписку! Вітаємо в StarlyStars ⭐. Що бажаєте придбати?",
        reply_markup=main_menu(),
    )
    await callback.answer()
  else:
    await callback.answer("❌ Ви ще не підписалися на канал!", show_alert=True)


@router.message(F.text == "💬 Відгуки")
async def btn_reviews(message: types.Message, bot: Bot):
  if not await check_subscription(message.from_user.id, bot):
    await message.answer(
        "⚠️ Спочатку підпишіться на канал!", reply_markup=sub_check_keyboard()
    )
    return
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔗 Перейти до відгуків",
              url="https://t.me/StarlyStars_UKR",
          )
      ]]
  )
  await message.answer("Наші відгуки:", reply_markup=kb)


@router.message(F.text == "⭐ Telegram Stars")
async def catalog_stars(message: types.Message, bot: Bot):
  if not await check_subscription(message.from_user.id, bot):
    await message.answer(
        "⚠️ Спочатку підпишіться на канал!", reply_markup=sub_check_keyboard()
    )
    return
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
      "Реквізити карти для оплати:\n"
      "5168745149435791\n"
      "Шевченко М.\n\n"
      "Після оплати, скиньте скріншот оплати сюди та очікуйте підтвердження."
  )
  await state.set_state(OrderState.waiting_for_screenshot)
  await state.update_data(
      item=f"{count} Stars ⭐", stars_add=int(count), prem_add=0
  )
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


@router.callback_query(F.data == "custom_stars")
async def custom_stars_prompt(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💬 Написати адміністратору", url="https://t.me/Mk_Bars"
              )
          ],
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")],
      ]
  )
  await callback.message.edit_text(
      "🔄 Своя кількість зірок\n\n"
      "Щоб придбати іншу кількість зірок, будь ласка, напишіть нашому"
      " адміністратору напряму:",
      reply_markup=kb,
  )
  await callback.answer()


@router.message(F.text == "💎 Telegram Premium")
async def catalog_prem(message: types.Message, bot: Bot):
  if not await check_subscription(message.from_user.id, bot):
    await message.answer(
        "⚠️ Спочатку підпишіться на канал!", reply_markup=sub_check_keyboard()
    )
    return
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
      "Реквізити карти для оплати:\n"
      "5168745149435791\n"
      "Шевченко М.\n\n"
      "Після оплати, скиньте скріншот оплати сюди та очікуйте підтвердження."
  )
  await state.set_state(OrderState.waiting_for_screenshot)
  await state.update_data(
      item=f"Telegram Premium ({period})", stars_add=0, prem_add=1
  )
  await callback.message.edit_text(text, reply_markup=back_button())
  await callback.answer()


@router.message(F.text == "👤 Профіль")
async def profile_handler(message: types.Message, bot: Bot):
  if not await check_subscription(message.from_user.id, bot):
    await message.answer(
        "⚠️ Спочатку підпишіться на канал!", reply_markup=sub_check_keyboard()
    )
    return
  user_id = message.from_user.id
  p = get_profile(user_id, message.from_user.full_name)

  ref_link = f"https://t.me/StarlyStars_bot?start=ref{user_id}"

  text = (
      "👤 Ваш профіль:\n\n"
      f"🆔 Номер акаунту (ID): {user_id}\n"
      f"📅 Дата створення: {p['reg_date']}\n"
      f"⭐ Всього придбано зірок: {p['stars_bought']}\n"
      f"💎 Всього придбано Premium: {p['prem_bought']}\n\n"
      "👥 Реферальна система:\n"
      f"Запрошено друзів: {p['referred_count']}\n"
      f"🔗 Ваше реферальне посилання:\n{ref_link}"
  )
  await message.answer(text, reply_markup=profile_keyboard())


@router.callback_query(F.data == "view_history")
async def view_history_cb(callback: types.CallbackQuery):
  user_id = callback.from_user.id
  p = get_profile(user_id)
  history = p["purchase_history"]

  if not history:
    await callback.answer(
        "У вас поки немає завершених замовлень 📦", show_alert=True
    )
    return

  history_text = "📦 Ваша історія покупок:\n\n"
  for order in history:
    history_text += f"▪️ Замовлення #{order['num']} — {order['item']}\n"

  await callback.message.answer(history_text)
  await callback.answer()


@router.message(F.text == "🛠 Підтримка")
async def support_handler(message: types.Message, state: FSMContext, bot: Bot):
  if not await check_subscription(message.from_user.id, bot):
    await message.answer(
        "⚠️ Спочатку підпишіться на канал!", reply_markup=sub_check_keyboard()
    )
    return
  await state.set_state(SupportState.waiting_for_message)
  await message.answer(
      "Напишіть будь ласка вашу проблему, адміністрація зв'яжеться з вами"
      " якомога скоріше.",
      reply_markup=back_button(),
  )


@router.message(SupportState.waiting_for_message)
async def send_support_to_admin(
    message: types.Message, state: FSMContext, bot: Bot
):
  user_name = message.from_user.full_name
  user_id = message.from_user.id
  text = (
      "📩 Нове звернення у підтримку!\n\n"
      f"👤 Від: {user_name} (ID: {user_id})\n"
      f"💬 Повідомлення: {message.text}"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="💬 Відповісти користувачу", url=f"tg://user?id={user_id}"
          )
      ]]
  )
  await bot.send_message(ADMIN_ID, text, reply_markup=kb)
  await state.clear()
  await message.answer(
      "Ваше повідомлення надіслано адміністрації!", reply_markup=main_menu()
  )


@router.message(OrderState.waiting_for_screenshot, F.photo)
async def receive_screenshot(
    message: types.Message, state: FSMContext, bot: Bot
):
  data = await state.get_data()
  item = data.get("item", "Товар")
  stars_add = data.get("stars_add", 0)
  prem_add = data.get("prem_add", 0)

  user_name = message.from_user.full_name
  user_id = message.from_user.id

  pending_orders[user_id] = {
      "user_name": user_name,
      "item": item,
      "stars_add": stars_add,
      "prem_add": prem_add,
  }

  info_text = (
      f"👤 Користувач: {user_name}\n"
      "⏳ Статус: Очікує підтвердження оплати...\n"
      f"📦 Кількість: {item}\n"
      f"🤖 Продавець: {BOT_USERNAME}"
  )
  await bot.send_message(ADMIN_ID, info_text)

  await bot.forward_message(
      chat_id=ADMIN_ID,
      from_chat_id=message.chat.id,
      message_id=message.message_id,
  )

  admin_kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="✅ Успішно", callback_data=f"approve_{user_id}"
          ),
          InlineKeyboardButton(
              text="❌ Відхилено", callback_data=f"decline_{user_id}"
          ),
      ]]
  )

  await bot.send_message(
      ADMIN_ID, text="👇 Керування оплатою вище:", reply_markup=admin_kb
  )

  await state.clear()
  await message.answer(
      "Почекайте поки триває перевірка оплати, це займає близько 5-60 хв",
      reply_markup=main_menu(),
  )


@router.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: types.CallbackQuery, bot: Bot):
  global order_counter
  user_id = int(callback.data.split("_")[1])

  order_info = pending_orders.get(
      user_id,
      {
          "user_name": "Користувач",
          "item": "Товар",
          "stars_add": 0,
          "prem_add": 0,
      },
  )

  order_counter += 1
  current_order_id = order_counter
  order_info["order_num"] = current_order_id

  stars_add = order_info["stars_add"]
  prem_add = order_info["prem_add"]
  item_name = order_info["item"]

  p = get_profile(user_id)
  p["stars_bought"] += stars_add
  p["prem_bought"] += prem_add
  p["purchase_history"].append({"num": current_order_id, "item": item_name})

  review_kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="✅ Так", callback_data=f"leave_yes_{user_id}"
          ),
          InlineKeyboardButton(
              text="❌ Ні", callback_data=f"leave_no_{user_id}"
          ),
      ]]
  )

  await bot.send_message(
      user_id,
      "✅ Ваша оплата успішна! Зірки/Преміум нараховані у ваш профіль.\n\n"
      "Бажаєте залишити відгук?",
      reply_markup=review_kb,
  )

  try:
    await callback.message.edit_text(
        text=f"✨ [СТАТУС: СХВАЛЕНО ✅ | Замовлення #{current_order_id}]"
    )
  except Exception:
    pass

  await callback.answer(f"Ви схвалили оплату! Замовлення #{current_order_id}")


@router.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: types.CallbackQuery, bot: Bot):
  user_id = int(callback.data.split("_")[1])
  pending_orders.pop(user_id, None)

  await bot.send_message(
      user_id, "❌ Вашу оплату було відхилено. Зверніться в підтримку."
  )
  try:
    await callback.message.edit_text(text="❌ [СТАТУС: ВІДХИЛЕНО ❌]")
  except Exception:
    pass
  await callback.answer("Ви відхилили оплату.")


@router.callback_query(F.data.startswith("leave_yes_"))
async def review_yes_cb(callback: types.CallbackQuery, state: FSMContext):
  await state.set_state(ReviewState.waiting_for_review_text)
  await callback.message.edit_text(
      "✍️ Напишіть ваш відгук нижче у повідомленні:"
  )
  await callback.answer()


@router.callback_query(F.data.startswith("leave_no_"))
async def review_no_cb(
    callback: types.CallbackQuery, state: FSMContext, bot: Bot
):
  user_id = callback.from_user.id
  user_name = callback.from_user.full_name

  order_info = pending_orders.get(
      user_id, {"order_num": 1, "item": "Зірки / Преміум"}
  )
  order_num = order_info.get("order_num", 1)
  purchased_item = order_info.get("item", "Зірки / Преміум")

  formatted_review = (
      f"👤 Користувач: {user_name}\n"
      f"🧾 Замовлення #{order_num}\n"
      f"📦 Кількість: {purchased_item}\n"
      "💬 Відгук: Вирішив промовчати 🤫\n"
      f"🤖 Продавець: {BOT_USERNAME}"
  )

  await bot.send_message(ADMIN_ID, formatted_review)
  pending_orders.pop(user_id, None)

  await state.clear()
  await callback.message.edit_text(
      "Дякуємо, що обрали StarlyStars ❤️\nГарного дня 💋"
  )
  await callback.answer()


@router.message(ReviewState.waiting_for_review_text)
async def receive_review_text(
    message: types.Message, state: FSMContext, bot: Bot
):
  user_id = message.from_user.id
  user_name = message.from_user.full_name
  review_text = message.text

  order_info = pending_orders.get(
      user_id, {"order_num": 1, "item": "Зірки / Преміум"}
  )
  order_num = order_info.get("order_num", 1)
  purchased_item = order_info.get("item", "Зірки / Преміум")

  formatted_review = (
      f"👤 Користувач: {user_name}\n"
      f"🧾 Замовлення #{order_num}\n"
      f"📦 Кількість: {purchased_item}\n"
      f"💬 Відгук: {review_text}\n"
      f"🤖 Продавець: {BOT_USERNAME}"
  )

  await bot.send_message(ADMIN_ID, formatted_review)
  pending_orders.pop(user_id, None)

  await state.clear()
  await message.answer(
      "Дякуємо за відгук ❤️\nГарного дня 💋", reply_markup=main_menu()
  )


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
  logging.info("Бот успішно запущено і готовий до роботи!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
