import telebot
import random
import datetime
import re
import os
import time
import logging
from threading import Thread

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token environment variable se lo
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable nahi mila!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Luhn Algorithm functions
def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10

def calculate_luhn(partial_number):
    check_digit = luhn_checksum(int(partial_number) * 10)
    return check_digit if check_digit == 0 else 10 - check_digit

def generate_card(bin_number, length=16, month=None, year=None, cvv=None):
    # BIN ke baad random digits fill karo
    while len(bin_number) < (length - 1):
        bin_number += str(random.randint(0, 9))
    
    # Check digit calculate karo
    check_digit = calculate_luhn(bin_number)
    card_number = bin_number + str(check_digit)
    
    # Expiry date
    if month is None or month == "rnd":
        month = str(random.randint(1, 12)).zfill(2)
    
    if year is None or year == "rnd":
        current_year = datetime.datetime.now().year
        year = str(random.randint(current_year, current_year + 5))
    
    # CVV
    if cvv is None or cvv == "rnd":
        if bin_number.startswith(('34', '37')):
            cvv_length = 4
        else:
            cvv_length = 3
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])
    
    return {
        'number': card_number,
        'month': month,
        'year': year,
        'cvv': cvv
    }

def generate_multiple_cards(bin_pattern, quantity=10, month=None, year=None, cvv=None):
    cards = []
    
    if 'x' in bin_pattern:
        x_count = bin_pattern.count('x')
        base_bin = bin_pattern.replace('x', '')
        
        for _ in range(quantity):
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(x_count)])
            full_bin = base_bin + random_part
            card = generate_card(full_bin, month=month, year=year, cvv=cvv)
            cards.append(card)
    else:
        for _ in range(quantity):
            card = generate_card(bin_pattern, month=month, year=year, cvv=cvv)
            cards.append(card)
    
    return cards

def format_cards(cards):
    return "\n".join([f"`{c['number']} | {c['month']}/{c['year']} | CVV:{c['cv v']}`" for c in cards])

# Bot Commands
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🤖 **CC GEN BOT** 🤖

Welcome! Main testing ke liye fake cards generate karta hoon.

**Commands:**
/help - Saari commands ka list
/gen <BIN> [quantity] - Cards generate karo

**Examples:**
/gen 457173 5 - 5 cards generate karo
/gen 457173xxxxxx 3 - Wildcard use karo

**Disclaimer:** Sirf testing ke liye!
"""
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 **COMMANDS** 📚

**Basic:**
/gen <BIN> [quantity]
Example: `/gen 457173 10`

**With Wildcards:**
/gen <BIN with x> [quantity]
Example: `/gen 457173xxxxxx 5`

**Note:** BIN kam se kam 6 digits ka hona chahiye.
Ek baar mein max 50 cards generate kar sakte ho.
"""
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['gen'])
def handle_gen(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Error: BIN number do! Example: `/gen 457173 5`", parse_mode="Markdown")
            return
        
        bin_pattern = parts[1]
        quantity = 10
        
        if len(parts) > 2 and parts[2].isdigit():
            quantity = int(parts[2])
            if quantity > 50:
                quantity = 50
                bot.reply_to(message, "⚠️ Max 50 cards ek baar mein, 50 generate kar raha hoon.")
        
        # Validate BIN
        bin_clean = re.sub(r'[^0-9x]', '', bin_pattern.lower())
        if len(bin_clean.replace('x', '')) < 6:
            bot.reply_to(message, "❌ Error: BIN number kam se kam 6 digits ka hona chahiye.")
            return
        
        # Processing message
        status = bot.reply_to(message, f"⏳ Generating {quantity} cards...")
        
        # Generate cards
        cards = generate_multiple_cards(bin_pattern, quantity=quantity)
        formatted = format_cards(cards)
        
        # Send result
        response = f"**Generated {quantity} Cards**\nBIN: `{bin_pattern}`\n\n{formatted}"
        bot.edit_message_text(response, message.chat.id, status.message_id, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    bot.reply_to(message, "❓ Command nahi samjha. /help likho commands ke liye.")

def keep_alive():
    """Bot ko alive rakhne ke liye"""
    while True:
        time.sleep(300)  # 5 minutes
        logger.info("Bot is running...")

# Main function
def main():
    logger.info("Bot starting...")
    logger.info(f"Bot token: {BOT_TOKEN[:5]}...")
    
    # Keep alive thread
    thread = Thread(target=keep_alive)
    thread.daemon = True
    thread.start()
    
    # Start bot
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(5)
        main()  # Restart on error

if __name__ == "__main__":
    main()
