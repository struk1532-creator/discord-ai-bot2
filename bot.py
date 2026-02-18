import discord
from discord.ext import commands
import google.generativeai as genai
import threading
import asyncio

# --- НАЛАШТУВАННЯ ---
TARGET_CHANNEL_ID = 1316723939896066087 
DISCORD_TOKEN = 'MTQ3MzQ2Mjc4NDU5NDI4MDY3Mw.Gt5UfF.oH-l_7bYnsfoKI0wUjbi5h4JVGo2FmmKDXkd28'
GEMINI_API_KEY = 'AIzaSyA79btwBHRXcamgw_FkXxYDOuBQylp4YTI'
# ---------------------

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

chat_sessions = {}
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# --- ВНУТРІШНЯ ДІАГНОСТИКА ---
async def check_health():
    try:
        # Тестовий запит до ШІ
        test = model.generate_content("hi")
        # Перевірка доступу до каналу
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if test.text and channel:
            return True
        return False
    except:
        return False

async def get_ai_answer(user_id, text):
    try:
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])
        chat = chat_sessions[user_id]
        response = chat.send_message(text)
        return response.text
    except Exception as e:
        return f"Помилка ШІ: {str(e)}"

def console_input():
    while True:
        try:
            msg = input("")
            if msg:
                asyncio.run_coroutine_threadsafe(send_from_console(msg), bot.loop)
        except EOFError: break

async def send_from_console(msg):
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel: await channel.send(msg)

@bot.event
async def on_ready():
    print(f'--- Бот {bot.user} запущено! ---')
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    
    if channel:
        # Проведення діагностики
        success = await check_health()
        if success:
            await channel.send("✅ **Бот працює**")
        else:
            await channel.send("❌ **Бот зламався**")
    
    print("Ви: ", end="", flush=True)
    threading.Thread(target=console_input, daemon=True).start()

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()
        
        # 1. РЕАКЦІЯ НА ІМ'Я (Владік, Влад)
        if "владік" in content_lower or "влад" in content_lower:
            await message.channel.send("Владік-лох")

        # 2. ВІДПОВІДЬ ШІ (Тільки на питання з '?')
        if message.content.strip().endswith('?'):
            print(f"\n[{message.author.display_name}]: {message.content}")
            async with message.channel.typing():
                answer = await get_ai_answer(message.author.id, message.content)
                await message.reply(answer.strip())
                print(f"[Бот відповів]: {answer.strip()}")
        
        print("Ви: ", end="", flush=True)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)