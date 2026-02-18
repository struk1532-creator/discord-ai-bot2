import os
import discord
import google.generativeai as genai
from discord.ext import commands
import http.server
import socketserver
import threading

# --- 1. МИТТЄВИЙ ЗАПУСК СЕРВЕРА (Для стабільності на Render) ---
PORT = int(os.environ.get("PORT", 10000))
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. НАЛАШТУВАННЯ ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TARGET_CHANNEL_ID = 1316723939896066087 

# Використовуємо чисту назву моделі
MODEL_NAME = 'gemini-1.5-flash'

genai.configure(api_key=GEMINI_API_KEY)

chat_histories = {} 
is_toxic_mode = False 

intents = discord.Intents.default()
intents.message_content = True 
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
        return f"❌ Помилка ШІ: {str(e)[:150]}"

@bot.event
async def on_ready():
    print(f'--- Бот {bot.user} онлайн ---')
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Бот запущено на стабільній моделі!**\n✅ Усі функції збережено.")

@bot.command(name="mode")
async def mode(ctx, mode_type: str):
    global is_toxic_mode, chat_histories
    is_toxic_mode = (mode_type.lower() == "toxic")
    status = "😈 ТОКСИЧНІСТЬ" if is_toxic_mode else "😇 Дружелюбність"
    await ctx.send(f"**Режим змінено на: {status}**")
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

        # Відповідь ШІ на питання з '?'
        if message.content.strip().endswith('?') and not message.content.startswith('!'):
            async with message.channel.typing():
                answer = await get_ai_answer(message)
                await message.reply(answer)

bot.run(DISCORD_TOKEN)
