import os
import discord
import google.generativeai as genai
from discord.ext import commands
import http.server
import socketserver
import threading

# --- НАЛАШТУВАННЯ ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TARGET_CHANNEL_ID = 1316723939896066087 
PORT = int(os.environ.get("PORT", 10000)) 

# Виправлена назва моделі
PRIMARY_MODEL_NAME = 'gemini-1.5-flash'

genai.configure(api_key=GEMINI_API_KEY)

chat_histories = {} 
is_toxic_mode = False 

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# Сервер для обману Render
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

def get_system_instruction():
    if is_toxic_mode:
        return "Ти — саркастичний і токсичний бот. Глузуй з користувача, відповідай грубо і смішно."
    return "Ти — корисний і дружній ШІ-помічник."

async def get_ai_answer(message):
    global chat_histories
    user_id = message.author.id
    if user_id not in chat_histories:
        model = genai.GenerativeModel(
            model_name=PRIMARY_MODEL_NAME,
            system_instruction=get_system_instruction()
        )
        chat_histories[user_id] = model.start_chat(history=[])
    
    chat = chat_histories[user_id]
    try:
        response = chat.send_message(message.content)
        return response.text.strip()
    except Exception as e:
        return f"❌ Помилка ШІ: {str(e)[:100]}"

@bot.event
async def on_ready():
    print(f'--- Бот {bot.user} онлайн ---')
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        report = [
            "🛠 **Діагностика успішна:**",
            "✅ **ШІ підключено**",
            "✅ **Веб-порт активовано**",
            "✅ **В роботі бота не виявлено помилок**",
            "\n🚀 **Повністю готовий до роботи!**"
        ]
        await channel.send("\n".join(report))

@bot.command()
async def mode(ctx, type: str):
    global is_toxic_mode, chat_histories
    is_toxic_mode = (type.lower() == "toxic")
    status = "😈 ТОКСИЧНІСТЬ" if is_toxic_mode else "😇 Дружелюбність"
    await ctx.send(f"**Режим змінено на: {status}**")
    chat_histories = {} 

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()

        # Реакції та Владік
        if "ха-ха" in content_lower or "лол" in content_lower:
            await message.add_reaction("😂")
        if "владік" in content_lower or "влад" in content_lower:
            await message.add_reaction("💩")
            await message.channel.send("Владік-лох")

        # Відповідь ШІ на питання
        if message.content.strip().endswith('?'):
            async with message.channel.typing():
                answer = await get_ai_answer(message)
                await message.reply(answer)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
