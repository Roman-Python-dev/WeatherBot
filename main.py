import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ========== КОНФИГ ==========
BOT_TOKEN = "8916434892:AAH1blgKzm8jiJQCAXkfh4mXmBlhY0OQu1Y"
WEATHER_API_KEY = "57e5313af6bb0c671dc7ef0e0eaa7f85"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


# ========== FSM ==========
class WeatherStates(StatesGroup):
    waiting_for_city = State()


# ========== ИНИЦИАЛИЗАЦИЯ ==========
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)


# ========== ЗАПРОС К API ==========
async def get_weather(city: str) -> dict:
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(OPENWEATHER_URL, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_data = await response.json()
                return {"error": error_data.get("message", "Город не найден")}


# ========== ФОРМАТИРОВАНИЕ ==========
def format_weather(data: dict) -> str:
    if "error" in data:
        return f"Ошибка: {data['error']}"

    city = data["name"]
    country = data["sys"]["country"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    description = data["weather"][0]["description"].capitalize()

    return (
        f"Погода в {city}, {country}\n"
        f"--------------------------\n"
        f"Температура: {temp:.1f} C\n"
        f"Ощущается как: {feels_like:.1f} C\n"
        f"Описание: {description}\n"
        f"Влажность: {humidity}%\n"
        f"Ветер: {wind_speed} м/с\n"
        f"Давление: {pressure} гПа"
    )


# ========== ХЕНДЛЕРЫ ==========

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я бот погоды.\n\n"
        "Чтобы узнать погоду, используй команду:\n"
        "/weather <город>\n\n"
        "Пример: /weather Москва\n\n"
        "Или просто отправь мне название города."
    )


@dp.message(Command("weather"))
async def weather_command(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        city = args[1]
        data = await get_weather(city)
        await message.answer(format_weather(data))
    else:
        await state.set_state(WeatherStates.waiting_for_city)
        await message.answer("Введите название города:")


@dp.message(WeatherStates.waiting_for_city)
async def handle_city_input(message: Message, state: FSMContext):
    city = message.text.strip()
    if not city:
        await message.answer("Введите название города текстом.")
        return
    data = await get_weather(city)
    await message.answer(format_weather(data))
    await state.clear()


@dp.message()
async def handle_text(message: Message):
    city = message.text.strip()
    if not city:
        return
    data = await get_weather(city)
    await message.answer(format_weather(data))


# ========== ЗАПУСК ==========
async def main():
    print("Бот погоды запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())