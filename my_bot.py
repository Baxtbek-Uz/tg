import os
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN", "8640724665:AAFHa2TA9nW0JP2c8W3jnYRuQtXe64RWXqQ")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "ce37637127d5f582518c458302470928")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

EMOJI_MAP = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
}

DESCRIPTION_UZ = {
    "clear sky": "Ochiq osmon",
    "few clouds": "Oz bulutli",
    "scattered clouds": "Tarqoq bulutlar",
    "broken clouds": "Bulutli",
    "overcast clouds": "Quyuq bulutli",
    "light rain": "Yengil yomg'ir",
    "moderate rain": "O'rtacha yomg'ir",
    "heavy intensity rain": "Kuchli yomg'ir",
    "very heavy rain": "Juda kuchli yomg'ir",
    "extreme rain": "Kuchli yomg'ir",
    "freezing rain": "Muzlatuvchi yomg'ir",
    "light intensity shower rain": "Yengil jala",
    "shower rain": "Jala",
    "heavy intensity shower rain": "Kuchli jala",
    "light snow": "Yengil qor",
    "snow": "Qor",
    "heavy snow": "Kuchli qor",
    "sleet": "Qor aralash yomg'ir",
    "thunderstorm": "Momaqaldiroq",
    "thunderstorm with light rain": "Yengil yomg'irli momaqaldiroq",
    "thunderstorm with rain": "Yomg'irli momaqaldiroq",
    "thunderstorm with heavy rain": "Kuchli yomg'irli momaqaldiroq",
    "mist": "Tuман",
    "fog": "Quyuq tuman",
    "haze": "Tutun",
    "dust": "Chang",
    "sand": "Qum bo'roni",
    "smoke": "Tutun",
    "tornado": "Tornado",
}

LANGUAGES = {
    "🇺🇿 O'zbek": "uz",
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
}

TEXTS = {
    "uz": {
        "welcome": "🌤️ Assalomu alaykum!\n\nOb-havo bilish uchun shahar nomini yuboring.",
        "ask_city": "Shahar nomini yuboring:",
        "not_found": "❌ Shahar topilmadi.\nIltimos, shahar nomini tekshirib qayta yuboring.",
        "api_error": "⚠️ API kalit xato yoki faol emas.",
        "other_error": "⚠️ Xatolik yuz berdi. Kod: ",
        "empty": "❗ Iltimos, shahar nomini yuboring.",
        "temp": "🌡️ Harorat",
        "feels": "🤔 His qilinadi",
        "humidity": "💧 Namlik",
        "wind": "💨 Shamol",
        "condition": "📋 Holat",
        "lang_changed": "✅ Til o'zgartirildi: O'zbek",
        "choose_lang": "Tilni tanlang:",
        "forecast_btn": "📅 5 kunlik ob-havo",
        "forecast_title": "📅 5 kunlik ob-havo",
        "current_btn": "🌤️ Hozirgi ob-havo",
        "enter_city_forecast": "5 kunlik ob-havo uchun shahar nomini yuboring:",
    },
    "ru": {
        "welcome": "🌤️ Привет!\n\nОтправьте название города, чтобы узнать погоду.",
        "ask_city": "Отправьте название города:",
        "not_found": "❌ Город не найден.\nПожалуйста, проверьте название и попробуйте снова.",
        "api_error": "⚠️ Ошибка API ключа.",
        "other_error": "⚠️ Произошла ошибка. Код: ",
        "empty": "❗ Пожалуйста, введите название города.",
        "temp": "🌡️ Температура",
        "feels": "🤔 Ощущается",
        "humidity": "💧 Влажность",
        "wind": "💨 Ветер",
        "condition": "📋 Состояние",
        "lang_changed": "✅ Язык изменён: Русский",
        "choose_lang": "Выберите язык:",
        "forecast_btn": "📅 Прогноз на 5 дней",
        "forecast_title": "📅 Прогноз на 5 дней",
        "current_btn": "🌤️ Текущая погода",
        "enter_city_forecast": "Отправьте название города для прогноза на 5 дней:",
    },
    "en": {
        "welcome": "🌤️ Hello!\n\nSend a city name to get the weather.",
        "ask_city": "Send a city name:",
        "not_found": "❌ City not found.\nPlease check the name and try again.",
        "api_error": "⚠️ API key error.",
        "other_error": "⚠️ An error occurred. Code: ",
        "empty": "❗ Please enter a city name.",
        "temp": "🌡️ Temperature",
        "feels": "🤔 Feels like",
        "humidity": "💧 Humidity",
        "wind": "💨 Wind",
        "condition": "📋 Condition",
        "lang_changed": "✅ Language changed: English",
        "choose_lang": "Choose language:",
        "forecast_btn": "📅 5-day forecast",
        "forecast_title": "📅 5-day forecast",
        "current_btn": "🌤️ Current weather",
        "enter_city_forecast": "Send a city name for 5-day forecast:",
    },
}

user_languages: dict[int, str] = {}
user_modes: dict[int, str] = {}

def get_lang(user_id: int) -> str:
    return user_languages.get(user_id, "uz")

def get_text(user_id: int, key: str) -> str:
    return TEXTS[get_lang(user_id)][key]

def translate_description(description: str, lang: str) -> str:
    if lang == "uz":
        return DESCRIPTION_UZ.get(description.lower(), description.capitalize())
    return description.capitalize()

def language_keyboard():
    buttons = [[KeyboardButton(lang)] for lang in LANGUAGES]
    buttons.append([KeyboardButton("🔙 Back")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def main_keyboard(user_id: int):
    buttons = [
        [KeyboardButton(get_text(user_id, "current_btn")), KeyboardButton(get_text(user_id, "forecast_btn"))],
        [KeyboardButton("🌍 Til / Язык / Language")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        get_text(user_id, "welcome"),
        reply_markup=main_keyboard(user_id)
    )

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        get_text(user_id, "choose_lang"),
        reply_markup=language_keyboard()
    )

async def get_coords(session: aiohttp.ClientSession, city: str):
    params = {
        "q": city,
        "limit": 1,
        "appid": WEATHER_API_KEY,
    }
    async with session.get(GEO_URL, params=params) as response:
        if response.status != 200:
            return None
        data = await response.json()
        if not data:
            return None
        return data[0]["lat"], data[0]["lon"], data[0]["name"], data[0]["country"]

async def get_weather(city: str, user_id: int) -> str:
    lang = get_lang(user_id)
    t = TEXTS[lang]

    async with aiohttp.ClientSession() as session:
        coords = await get_coords(session, city)
        if not coords:
            return t["not_found"]

        lat, lon, city_name, country = coords

        params = {
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": lang,
        }

        async with session.get(WEATHER_URL, params=params) as response:
            if response.status == 401:
                return t["api_error"]
            if response.status != 200:
                return t["other_error"] + str(response.status)

            data = await response.json()

            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            condition = data["weather"][0]["main"]
            description = data["weather"][0]["description"]
            description = translate_description(description, lang)
            emoji = EMOJI_MAP.get(condition, "🌡️")

            return (
                f"{emoji} {city_name}, {country}\n\n"
                f"{t['temp']}: {temp:.1f}°C\n"
                f"{t['feels']}: {feels_like:.1f}°C\n"
                f"{t['humidity']}: {humidity}%\n"
                f"{t['wind']}: {wind_speed} m/s\n"
                f"{t['condition']}: {description}"
            )

async def get_forecast(city: str, user_id: int) -> str:
    lang = get_lang(user_id)
    t = TEXTS[lang]

    async with aiohttp.ClientSession() as session:
        coords = await get_coords(session, city)
        if not coords:
            return t["not_found"]

        lat, lon, city_name, country = coords

        params = {
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": lang,
            "cnt": 40,
        }

        async with session.get(FORECAST_URL, params=params) as response:
            if response.status == 401:
                return t["api_error"]
            if response.status != 200:
                return t["other_error"] + str(response.status)

            data = await response.json()

            daily: dict[str, dict] = {}
            for item in data["list"]:
                date = item["dt_txt"].split(" ")[0]
                if date not in daily:
                    daily[date] = {
                        "temps": [],
                        "condition": item["weather"][0]["main"],
                        "description": item["weather"][0]["description"],
                    }
                daily[date]["temps"].append(item["main"]["temp"])

            lines = [f"{t['forecast_title']} — {city_name}, {country}\n"]
            for date, info in list(daily.items())[:5]:
                day = datetime.strptime(date, "%Y-%m-%d").strftime("%d %b")
                min_t = min(info["temps"])
                max_t = max(info["temps"])
                emoji = EMOJI_MAP.get(info["condition"], "🌡️")
                description = translate_description(info["description"], lang)
                lines.append(f"{emoji} {day}: {min_t:.0f}°C — {max_t:.0f}°C, {description}")

            return "\n".join(lines)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if text == "🌍 Til / Язык / Language":
        await change_language(update, context)
        return

    if text in LANGUAGES:
        user_languages[user_id] = LANGUAGES[text]
        await update.message.reply_text(
            get_text(user_id, "lang_changed"),
            reply_markup=main_keyboard(user_id)
        )
        return

    if text == "🔙 Back":
        user_modes.pop(user_id, None)
        await update.message.reply_text(
            get_text(user_id, "ask_city"),
            reply_markup=main_keyboard(user_id)
        )
        return

    if text == get_text(user_id, "current_btn"):
        user_modes[user_id] = "current"
        await update.message.reply_text(
            get_text(user_id, "ask_city"),
            reply_markup=main_keyboard(user_id)
        )
        return

    if text == get_text(user_id, "forecast_btn"):
        user_modes[user_id] = "forecast"
        await update.message.reply_text(
            get_text(user_id, "enter_city_forecast"),
            reply_markup=main_keyboard(user_id)
        )
        return

    if not text:
        await update.message.reply_text(get_text(user_id, "empty"))
        return

    await update.message.reply_chat_action("typing")

    mode = user_modes.get(user_id, "current")

    if mode == "forecast":
        result = await get_forecast(text, user_id)
    else:
        result = await get_weather(text, user_id)

    await update.message.reply_text(result, reply_markup=main_keyboard(user_id))

def main():
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=60,
        connection_pool_size=16,
    )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .request(request)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🌤️ Ob-havo bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()  