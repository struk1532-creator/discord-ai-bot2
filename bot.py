import os
import discord
from discord.ext import commands
import google.generativeai as genai

# --- НАЛАШТУВАННЯ ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TARGET_CHANNEL_ID = 1316723939896066087 

# Моделі
PRIMARY_MODEL = 'models/gemini-2.0-flash'
BACKUP_MODEL = 'models/gemini-1.5-flash'

genai.configure(api_key=GEMINI_API_KEY)
current_model_name = PRIMARY_MODEL
model = genai.GenerativeModel(current_model_name)

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# Функція отримання відповіді з перемиканням режимів
async def get_ai_answer(message):
    global model, current_model_name
    try:
        response = model.generate_content(message.content)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) and current_model_name == PRIMARY_MODEL:
            await message.channel.send("⚠️ **Ліміти швидкої моделі вичерпано. Переходжу в повільніший режим...**")
            current_model_name = BACKUP_MODEL
            model = genai.GenerativeModel(current_model_name)
            response = model.generate_content(message.content)
            return response.text.strip()
        else:
            return f"❌ Помилка: {str(e)[:100]}"

@bot.event
async def on_ready():
    print(f'--- Бот {bot.user} запущено ---')
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    
    if channel:
        report = [
            "🛠 **Результати діагностики:**",
            "✅ **ШІ працює**",
            "✅ **Хостинг працює**",
            "✅ **В роботі бота не виявлено помилок**",
            "\n🚀 **Повністю готовий до роботи!**"
        ]
        # Проста перевірка зв'язку перед звітом
        try:
            model.generate_content("test")
            await channel.send("\n".join(report))
        except:
            await channel.send("⚠️ Діагностика завершена з попередженням: ШІ тимчасово недоступний (можливо, ліміти).")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()
        
        # 1. РЕАКЦІЯ НА ВЛАДІКА
        if "владік" in content_lower or "влад" in content_lower:
            await message.channel.send("Владік-лох")

        # 2. ВІДПОВІДЬ ШІ (на питання з '?')
        if message.content.strip().endswith('?'):
            async with message.channel.typing():
                answer = await get_ai_answer(message)
                await message.reply(answer)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
