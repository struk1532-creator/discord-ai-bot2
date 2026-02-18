import os
import sys
import discord
import google.generativeai as genai
from discord.ext import commands
import http.server
import socketserver
import threading

# --- 1. ПЕРЕВІРКА ЗАПУСКУ (Діагностика для логів Render) ---
print("--- Ініціалізація бота... ---")

# Зчитуємо ключі
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TARGET_CHANNEL_ID = 1316723939896066087 
PORT = int(os.environ.get("PORT", 10000))

# Перевірка наявності ключів
if not DISCORD_TOKEN:
    print("❌ ПОМИЛКА: DISCORD_TOKEN не знайдено в Environment Variables!")
if not GEMINI_API_KEY:
    print("❌ ПОМИЛКА: GEMINI_API_KEY не знайдено в Environment Variables!")
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    sys.exit(1) # Зупиняємо скрипт, якщо немає ключів

# --- 2. СЕРВЕР ДЛЯ RENDER (Щоб не було Timeout) ---
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"✅ Веб-сервер запущено на порту {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ Попередження сервера: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 3. НАЛАШТУВАННЯ ШІ (Gemini 2.0 Flash) ---
# Використовуємо 2.0, бо на 1.5 у тебе була помилка 404
MODEL_NAME = 'gemini-2.0-flash'
genai.configure(api_key=GEMINI_API_KEY)

chat_histories = {} 
is_toxic_mode = False 

intents = discord.Intents.default()
intents.message_content = True # НЕ ЗАБУДЬ УВІМКНУТИ В ПАНЕЛІ DISCORD!
bot = commands.Bot(command_prefix="!", intents=intents)

def get_system_instruction():
    if is_toxic_mode:
        return "Ти — саркастичний і токсичний бот. Глузуй з користувача, відповідай грубо і смішно."
    return "Ти — корисний і дружній ШІ-помічник."

async def get_ai_answer(message):
    global chat_histories
    user_id = message.author.id
    if user_id not in chat_histories:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=get_system_instruction()
        )
        chat_histories[user_id] = model.start_chat(history=[])
    
    chat = chat_histories[user_id]
    try:
        response = chat.send_message(message.content)
        return response.text.strip()
    except Exception as e:
        return f"❌ Помилка ШІ (модель {MODEL_NAME}): {str(e)[:150]}"

# --- 4. ПОДІЇ ТА КОМАНДИ ---

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} успішно підключився до Discord!')
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Бот перезібраний з Gemini 2.0!**\n\nЯ пам'ятаю все:\n💩 Владік під прицілом\n😈 Режим `!mode toxic` працює\n🧠 Пам'ять діалогу активована")

@bot.command(name="mode")
async def mode(ctx, type: str):
    global is_toxic_mode, chat_histories
    is_toxic_mode = (type.lower() == "toxic")
    status = "😈 ТОКСИЧНІСТЬ" if is_toxic_mode else "😇 Дружелюбність"
    await ctx.send(f"**Характер змінено на: {status}**")
    chat_histories = {} 

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    await bot.process_commands(message)

    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()

        # Реакція на Владіка (збережено)
        if "владік" in content_lower or "влад" in content_lower:
            await message.add_reaction("💩")
            await message.channel.send("Владік-лох")
        
        if "ха-ха" in content_lower or "лол" in content_lower:
            await message.add_reaction("😂")

        # Питання до ШІ
        if message.content.strip().endswith('?') and not message.content.startswith('!'):
            async with message.channel.typing():
                answer = await get_ai_answer(message)
                await message.reply(answer)

# ЗАПУСК
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ КРИТИЧНА ПОМИЛКА ЗАПУСКУ: {e}")
