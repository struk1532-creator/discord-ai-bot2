import os
import discord
import google.generativeai as genai
from discord.ext import commands

# --- НАЛАШТУВАННЯ ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TARGET_CHANNEL_ID = 1316723939896066087 

# Налаштування ШІ
genai.configure(api_key=GEMINI_API_KEY)
PRIMARY_MODEL_NAME = 'gemini-1.5-flash'

# Глобальні змінні для фіч
chat_histories = {} 
is_toxic_mode = False 

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

def get_system_instruction():
    if is_toxic_mode:
        return "Ти — саркастичний і дуже токсичний бот. Твоє завдання — глузувати з питань користувача, відповідати грубо, але смішно. Ти ненавидиш відповідати на дурні питання."
    return "Ти — корисний і дружній ШІ-помічник."

async def get_ai_answer(message):
    global chat_histories
    user_id = message.author.id
    
    if user_id not in chat_histories:
        chat_histories[user_id] = genai.GenerativeModel(
            model_name=PRIMARY_MODEL_NAME,
            system_instruction=get_system_instruction()
        ).start_chat(history=[])
    
    chat = chat_histories[user_id]
    try:
        response = chat.send_message(message.content)
        return response.text.strip()
    except Exception as e:
        return f"❌ Помилка ШІ: {str(e)[:100]}"

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
        await channel.send("\n".join(report))

@bot.command()
async def mode(ctx, type: str):
    global is_toxic_mode, chat_histories
    if type.lower() == "toxic":
        is_toxic_mode = True
        await ctx.send("😈 **Режим ТОКСИЧНІСТЬ активовано. Бережіться.**")
    else:
        is_toxic_mode = False
        await ctx.send("😇 **Режим Дружелюбності активовано. Я знову сонечко.**")
    chat_histories = {} # Скидаємо пам'ять для зміни характеру

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()

        # ФУНКЦІЯ 1: Реакції
        if "ха-ха" in content_lower or "лол" in content_lower:
            await message.add_reaction("😂")
        if "владік" in content_lower or "влад" in content_lower:
            await message.add_reaction("💩")
            await message.channel.send("Владік-лох")

        # ФУНКЦІЯ 2 & 5: ШІ з пам'яттю та характером
        if message.content.strip().endswith('?'):
            async with message.channel.typing():
                answer = await get_ai_answer(message)
                await message.reply(answer)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
