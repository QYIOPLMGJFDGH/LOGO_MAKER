import os
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageColor
from random import randint
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User data store
user_data_store = {}

# Adjust font size dynamically
def get_dynamic_font(image, text, max_width, max_height, font_path):
    draw = ImageDraw.Draw(image)
    font_size = 100
    while font_size > 10:
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = draw.textsize(text, font=font)
        if text_width <= max_width and text_height <= max_height:
            return font
        font_size -= 5
    return font

# Define inline keyboard for adjustments with color and font options
def get_adjustment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Left", callback_data="move_left"),
         InlineKeyboardButton("➡️ Right", callback_data="move_right")],
        [InlineKeyboardButton("⬆️ Up", callback_data="move_up"),
         InlineKeyboardButton("⬇️ Down", callback_data="move_down")],
        [InlineKeyboardButton("🔍 Increase", callback_data="increase_size"),
         InlineKeyboardButton("🔎 Decrease", callback_data="decrease_size")],
        
        # Color selection buttons
        [InlineKeyboardButton("🔴 Red", callback_data="color_red"),
         InlineKeyboardButton("🔵 Blue", callback_data="color_blue"),
         InlineKeyboardButton("🟢 Green", callback_data="color_green"),
         InlineKeyboardButton("⚫ Black", callback_data="color_black"),
         InlineKeyboardButton("🟡 Yellow", callback_data="color_yellow"),
         InlineKeyboardButton("🟠 Orange", callback_data="color_orange"),
         InlineKeyboardButton("🟣 Purple", callback_data="color_purple"),
         InlineKeyboardButton("🟤 Brown", callback_data="color_brown")],
        
        [InlineKeyboardButton("🟤 Maroon", callback_data="color_maroon"),
         InlineKeyboardButton("💖 Pink", callback_data="color_pink"),
         InlineKeyboardButton("🟡 Gold", callback_data="color_gold"),
         InlineKeyboardButton("🟢 Lime", callback_data="color_lime"),
         InlineKeyboardButton("🟩 Mint", callback_data="color_mint"),
         InlineKeyboardButton("🟦 Sky Blue", callback_data="color_sky_blue"),
         InlineKeyboardButton("🟩 Teal", callback_data="color_teal"),
         InlineKeyboardButton("🟪 Violet", callback_data="color_violet")],
        
        [InlineKeyboardButton("🔶 Amber", callback_data="color_amber"),
         InlineKeyboardButton("🔷 Turquoise", callback_data="color_turquoise"),
         InlineKeyboardButton("🟧 Peach", callback_data="color_peach"),
         InlineKeyboardButton("🔴 Burgundy", callback_data="color_burgundy"),
         InlineKeyboardButton("🟤 Coffee", callback_data="color_coffee"),
         InlineKeyboardButton("🟡 Mustard", callback_data="color_mustard")],

        # Font selection buttons
        [InlineKeyboardButton("Deadly Advance Italic", callback_data="font_deadly_advance_italic"),
         InlineKeyboardButton("Deadly Advance", callback_data="font_deadly_advance"),
         InlineKeyboardButton("Trick or Treats", callback_data="font_trick_or_treats"),
         InlineKeyboardButton("Vampire Wars Italic", callback_data="font_vampire_wars_italic"),
         InlineKeyboardButton("Lobster", callback_data="font_lobster")]
    ])

# Add text to image with "brushstroke" effect
async def add_text_to_image(photo_path, text, font_path, text_position, size_multiplier, text_color):
    try:
        user_image = Image.open(photo_path).convert("RGBA")
        max_width, max_height = user_image.size

        # Adjust font size based on size_multiplier
        font = get_dynamic_font(user_image, text, max_width, max_height, font_path)
        font = ImageFont.truetype(font_path, int(font.size * size_multiplier))
        
        draw = ImageDraw.Draw(user_image)
        text_width, text_height = draw.textsize(text, font=font)
        
        # Apply position adjustments
        x = text_position[0]
        y = text_position[1]

        # Brushstroke effect (slightly offset multiple layers of text to create a stroke effect)
        num_strokes = 8  # Number of brush strokes
        for i in range(num_strokes):
            offset_x = randint(-5, 5)  # Random horizontal offset
            offset_y = randint(-5, 5)  # Random vertical offset
            # Add a blurred stroke effect by drawing text in slightly different positions
            draw.text((x + offset_x, y + offset_y), text, font=font, fill="white")  # White outline effect
        
        # Main text in the chosen color
        draw.text((x, y), text, font=font, fill=text_color)

        # Save the image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            output_path = temp_file.name
            user_image.save(output_path, "PNG")
        
        return output_path
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return None

# Save user data
async def save_user_data(user_id, data):
    user_data_store[user_id] = data
    logger.info(f"User {user_id} data saved: {data}")

# Get user data
async def get_user_data(user_id):
    return user_data_store.get(user_id, None)

# Initialize the Pyrogram Client
session_name = "logo_creator_bot"
app = Client(
    session_name,
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    workdir=os.getcwd()
)

@app.on_message(filters.command("start"))
async def start_command(_, message: Message) -> None:
    welcome_text = (
        "👋 Welcome to the Logo Creator Bot!\n\n"
        "With this bot, you can create a custom logo by sending a photo and adding text to it!\n"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Join 👋", url="https://t.me/BABY09_WORLD")]])
    await message.reply_text(welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

@app.on_message(filters.photo & filters.private)
async def photo_handler(_, message: Message) -> None:
    media = message
    file_size = media.photo.file_size if media.photo else 0
    if file_size > 200 * 1024 * 1024:
        return await message.reply_text("Please provide a photo under 200MB.")
    try:
        text = await message.reply("Processing...")
        local_path = await media.download()
        await text.edit_text("Processing your logo...")
        await save_user_data(message.from_user.id, {'photo_path': local_path, 'text': '', 'text_position': (0, 0), 'size_multiplier': 1, 'text_color': 'red', 'font': 'fonts/Deadly Advance.ttf'})
        await message.reply_text("Please send the text you want for your logo.")
    except Exception as e:
        logger.error(e)
        await text.edit_text("File processing failed.")

@app.on_message(filters.text & filters.private)
async def text_handler(_, message: Message) -> None:
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        await message.reply_text("Please send a photo first.")
        return
    
    if user_data['text']:
        await message.reply_text("You have already entered text for your logo. Proceed with position adjustments.")
        return

    user_text = message.text.strip()
    if not user_text:
        await message.reply_text("You need to provide text for your logo.")
        return
    user_data['text'] = user_text
    await save_user_data(user_id, user_data)

    # Generate logo and show adjustment options
    font_path = user_data['font']  # Default to Deadly Advance font if not set
    output_path = await add_text_to_image(user_data['photo_path'], user_text, font_path, user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']))

    if output_path is None:
        await message.reply_text("There was an error generating the logo. Please try again.")
        return

    await message.reply_photo(photo=output_path, reply_markup=get_adjustment_keyboard())

@app.on_callback_query()
async def callback_handler(_, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data or not user_data.get("photo_path"):
        await callback_query.answer("Please upload a photo first.", show_alert=True)
        return

    # Adjust position, size, or color based on button pressed
    if callback_query.data == "move_left":
        user_data['text_position'] = (user_data['text_position'][0] - 20, user_data['text_position'][1])
    elif callback_query.data == "move_right":
        user_data['text_position'] = (user_data['text_position'][0] + 20, user_data['text_position'][1])
    elif callback_query.data == "move_up":
        user_data['text_position'] = (user_data['text_position'][0], user_data['text_position'][1] - 20)
    elif callback_query.data == "move_down":
        user_data['text_position'] = (user_data['text_position'][0], user_data['text_position'][1] + 20)
    elif callback_query.data == "increase_size":
        user_data['size_multiplier'] *= 1.1
    elif callback_query.data == "decrease_size":
        user_data['size_multiplier'] *= 0.9
    elif callback_query.data == "color_red":
        user_data['text_color'] = "red"
    elif callback_query.data == "color_blue":
        user_data['text_color'] = "blue"
    elif callback_query.data == "color_green":
        user_data['text_color'] = "green"
    elif callback_query.data == "color_black":
        user_data['text_color'] = "black"
    elif callback_query.data == "color_yellow":
        user_data['text_color'] = "yellow"
    elif callback_query.data == "color_orange":
        user_data['text_color'] = "orange"
    elif callback_query.data == "color_purple":
        user_data['text_color'] = "purple"
    elif callback_query.data == "color_brown":
        user_data['text_color'] = "brown"
    elif callback_query.data == "color_maroon":
        user_data['text_color'] = "maroon"
    elif callback_query.data == "color_pink":
        user_data['text_color'] = "pink"
    elif callback_query.data == "color_gold":
        user_data['text_color'] = "gold"
    elif callback_query.data == "color_lime":
        user_data['text_color'] = "lime"
    elif callback_query.data == "color_mint":
        user_data['text_color'] = "mint"
    elif callback_query.data == "color_sky_blue":
        user_data['text_color'] = "skyblue"
    elif callback_query.data == "color_teal":
        user_data['text_color'] = "teal"
    elif callback_query.data == "color_violet":
        user_data['text_color'] = "violet"
    elif callback_query.data == "color_amber":
        user_data['text_color'] = "amber"
    elif callback_query.data == "color_turquoise":
        user_data['text_color'] = "turquoise"
    elif callback_query.data == "color_peach":
        user_data['text_color'] = "peach"
    elif callback_query.data == "color_burgundy":
        user_data['text_color'] = "burgundy"
    elif callback_query.data == "color_coffee":
        user_data['text_color'] = "coffee"
    elif callback_query.data == "color_mustard":
        user_data['text_color'] = "mustard"

    # Font selection logic
    if callback_query.data == "font_deadly_advance_italic":
        user_data['font'] = "fonts/Deadly Advance Italic (1).ttf"
    elif callback_query.data == "font_deadly_advance":
        user_data['font'] = "fonts/Deadly Advance.ttf"
    elif callback_query.data == "font_trick_or_treats":
        user_data['font'] = "fonts/Trick or Treats.ttf"
    elif callback_query.data == "font_vampire_wars_italic":
        user_data['font'] = "fonts/Vampire Wars Italic.ttf"
    elif callback_query.data == "font_lobster":
        user_data['font'] = "fonts/FIGHTBACK.ttf"

    await save_user_data(user_id, user_data)

    # Regenerate the logo with the new adjustments
    font_path = user_data.get("font", "fonts/Deadly Advance.ttf")  # Default to Deadly Advance font if no font is set
    output_path = await add_text_to_image(user_data['photo_path'], user_data['text'], font_path, user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']))

    if output_path is None:
        await callback_query.message.reply_text("There was an error generating the logo. Please try again.")
        return

    # Keep the buttons and update the image
    await callback_query.message.edit_media(InputMediaPhoto(media=output_path, caption="Here is your logo with the changes!"), reply_markup=get_adjustment_keyboard())
    await callback_query.answer()

if __name__ == "__main__":
    app.run()
    
