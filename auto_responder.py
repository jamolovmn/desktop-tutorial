"""
Telegram Auto-Responder with Groq AI
Automatically responds to incoming Telegram messages using AI
"""

import os
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import User
import httpx

load_dotenv()

# Telegram credentials
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

# Groq API - Multiple keys for rotation
GROQ_API_KEYS = [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
    os.getenv("GROQ_API_KEY_4"),
]
# Filter out None values
GROQ_API_KEYS = [k for k in GROQ_API_KEYS if k]
current_key_index = 0
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_next_api_key():
    """Rotate to next API key"""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(GROQ_API_KEYS)
    print(f"🔄 API kalit o'zgartirildi: #{current_key_index + 1}")
    return GROQ_API_KEYS[current_key_index]

def get_current_api_key():
    """Get current API key"""
    return GROQ_API_KEYS[current_key_index]

# System prompt for AI
SYSTEM_PROMPT = """Sen umumiy maqsadli aqlli AI yordamchisan.

Sening roling:
Sen inson ekspert kabi o'ylaysan, fikr yuritasan, tushuntirasan, yo'l ko'rsatasan va muammolarni hal qilasan.

Sen yordam bera olasan:
• Veb-saytlar
• Akkauntlar  
• Dashboardlar
• Biznes
• Ta'lim
• Texnik muammolar
• Yozish
• G'oyalar
• Avtomatlashtirish
• Foydalanuvchi so'ragan har qanday narsa

Foydalanuvchi savol berganda:
1. Ularning niyatini tushun
2. Muammoni qismlarga bo'l
3. Aniq yechim ber
4. Keyingi qadamlarni taklif qil

Uslub:
• Do'stona
• Aqlli
• Xotirjam
• Professional

Sen bitta veb-sayt bilan chegaralanmagan.
Sen to'liq raqamli yordamchisan.

Maqsading:
Foydalanuvchiga maqsadiga tezroq va osonroq erishishga yordam ber.

Qoidalar:
- Javob FAFAQAT 1 TA GAP bo‘lishi shart.
- Maksimal 20 ta so‘z.
- Hech qachon izoh bermagin.
- Hech qachon ro‘yxat qilma.
- Hech qachon ortiqcha tushuntirma.
- Faqat aniq javob ber.
- Agar savol tushunarsiz bo‘lsa 1 ta aniqlashtiruvchi savol ber.

Format:
Javob faqat oddiy matn bo‘lsin.
Hech qanday qo‘shimcha yozma."""

# Store conversation history per chat
chat_histories = {}

# Bot control variables
bot_paused = False
ignored_users = set()  # Set of user IDs to ignore

# Create client
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
else:
    client = TelegramClient(TELEGRAM_SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)


# Command handler - only responds to YOUR commands (outgoing messages)
@client.on(events.NewMessage(outgoing=True, pattern=r'^/'))
async def handle_commands(event):
    """Handle bot control commands"""
    global bot_paused, ignored_users
    
    command = event.text.lower().split()[0]
    args = event.text.split()[1:] if len(event.text.split()) > 1 else []
    
    if command == "/pause":
        bot_paused = True
        await event.edit("⏸️ Bot to'xtatildi")
        print("⏸️ Bot PAUSED")
        
    elif command == "/resume" or command == "/start":
        bot_paused = False
        await event.edit("▶️ Bot ishga tushdi")
        print("▶️ Bot RESUMED")
        
    elif command == "/status":
        status = "⏸️ To'xtatilgan" if bot_paused else "✅ Ishlayapti"
        ignored = ", ".join(str(u) for u in ignored_users) if ignored_users else "Yo'q"
        await event.edit(f"📊 Status: {status}\n🚫 Ignored: {ignored}")
        
    elif command == "/ignore":
        if event.reply_to:
            replied = await event.get_reply_message()
            if replied and replied.sender_id:
                ignored_users.add(replied.sender_id)
                await event.edit(f"🚫 {replied.sender_id} ignore qilindi")
                print(f"🚫 Ignored user: {replied.sender_id}")
        elif args:
            try:
                user_id = int(args[0])
                ignored_users.add(user_id)
                await event.edit(f"🚫 {user_id} ignore qilindi")
            except:
                await event.edit("❌ User ID noto'g'ri")
        else:
            await event.edit("❌ Reply qiling yoki ID yozing: /ignore 123456")
            
    elif command == "/unignore":
        if args:
            try:
                user_id = int(args[0])
                ignored_users.discard(user_id)
                await event.edit(f"✅ {user_id} ignore'dan chiqarildi")
            except:
                await event.edit("❌ User ID noto'g'ri")
        else:
            await event.edit("❌ ID yozing: /unignore 123456")


async def get_ai_response(chat_id: int, user_message: str, sender_name: str) -> Optional[str]:
    """Get AI response from Groq"""
    
    # Get or create chat history
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    
    history = chat_histories[chat_id]
    
    # Add user message to history
    history.append({
        "role": "user",
        "content": f"{sender_name}: {user_message}"
    })
    
    # Keep only last 10 messages
    if len(history) > 10:
        history = history[-10:]
        chat_histories[chat_id] = history
    
    # Prepare messages for API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            # Try each API key until one works
            for attempt in range(len(GROQ_API_KEYS)):
                current_key = get_current_api_key()
                
                response = await http_client.post(
                    GROQ_API_URL,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {current_key}"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "max_tokens": 40,
                        "temperature": 0.2
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"]
                    
                    # Add AI response to history
                    history.append({
                        "role": "assistant", 
                        "content": ai_response
                    })
                    
                    return ai_response
                
                elif response.status_code == 429:
                    # Rate limit - switch to next key
                    print(f"⚠️ API #{current_key_index + 1} limit tugadi")
                    get_next_api_key()
                    await asyncio.sleep(1)  # Small delay before retry
                    continue
                    
                else:
                    print(f"❌ Groq API Error: {response.status_code}")
                    return None
            
            # All keys exhausted
            print("❌ Barcha API kalitlar limit tugadi!")
            return "⏳ Hozir band, biroz kutib turing."
                
    except Exception as e:
        print(f"❌ Error getting AI response: {e}")
        return None


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    """Handle incoming messages"""
    global bot_paused, ignored_users
    
    # Skip if bot is paused
    if bot_paused:
        return
    
    # Skip channels
    if event.is_channel and not event.is_group:
        return
    
    # Skip if no text
    if not event.text:
        return
    
    # Skip ignored users
    if event.sender_id in ignored_users:
        print(f"🚫 Ignored message from {event.sender_id}")
        return
    
    # Get my user ID
    me = await client.get_me()
    my_id = me.id
    
    # For groups: only respond if someone replies to MY message
    if event.is_group:
        # Check if this is a reply to my message
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            if replied_msg and replied_msg.sender_id == my_id:
                # Someone replied to my message - respond!
                pass
            else:
                return  # Not a reply to me, skip
        else:
            return  # Not a reply at all, skip
    
    # Get sender info
    sender = await event.get_sender()
    if not isinstance(sender, User):
        return
    
    # Skip bots - don't respond to other bots
    if sender.bot:
        return
    
    sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "Unknown"
    chat_id = event.chat_id
    
    is_group = "guruh" if event.is_group else "shaxsiy"
    print(f"\n📨 Yangi xabar ({is_group}): {sender_name}")
    print(f"   Xabar: {event.text}")
    
    # Get AI response
    ai_response = await get_ai_response(chat_id, event.text, sender_name)
    
    if ai_response:
        # Add small delay to seem more natural
        await asyncio.sleep(1)
        
        # Send response
        await event.respond(ai_response)
        print(f"✅ Javob yuborildi: {ai_response}")
    else:
        print("⚠️ Javob olinmadi")


async def main():
    """Main function"""
    print("\n" + "="*50)
    print("🤖 TELEGRAM AUTO-RESPONDER")
    print("="*50)
    
    if not GROQ_API_KEYS:
        print("❌ GROQ_API_KEY topilmadi!")
        return
    
    await client.start()
    
    me = await client.get_me()
    print(f"✅ {me.first_name} sifatida ulandi")
    print("📱 Shaxsiy xabarlarga avtomatik javob beriladi...")
    print("🛑 To'xtatish uchun Ctrl+C bosing")
    print("="*50 + "\n")
    
    # Keep running
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Auto-responder to'xtatildi")
