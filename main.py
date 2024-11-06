import os
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from random import randint
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto
from config import Config
from buttons import get_adjustment_keyboard  # Importing the button function

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User data store (this will be temporary storage)
user_data_store = {}

# Function to adjust font size dynamically
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

# Function to add text to the image with brushstroke and blur
async def add_text_to_image(photo_path, text, font_path, text_position, size_multiplier, text_color, blur_radius):
    try:
        user_image = Image.open(photo_path).convert("RGBA")
        max_width, max_height = user_image.size

        # Adjust font size based on size_multiplier
        font = get_dynamic_font(user_image, text, max_width, max_height, font_path)
        font = ImageFont.truetype(font_path, int(font.size * size_multiplier))

        # Create a new image for drawing text (will be placed on top of the original)
        text_image = Image.new("RGBA", user_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_image)
        text_width, text_height = draw.textsize(text, font=font)

        # Apply position adjustments
        x = text_position[0]
        y = text_position[1]

        # Brushstroke effect (slightly offset multiple layers of text to create a stroke effect)
        num_strokes = 8
        for i in range(num_strokes):
            offset_x = randint(-5, 5)
            offset_y = randint(-5, 5)
            draw.text((x + offset_x, y + offset_y), text, font=font, fill="white")  # White outline effect

        # Main text in the chosen color
        draw.text((x, y), text, font=font, fill=text_color)

        # Blur the background (excluding the text area)
        blurred_image = user_image.filter(ImageFilter.GaussianBlur(blur_radius))

        # Composite the blurred image with the text image
        final_image = Image.alpha_composite(blurred_image, text_image)

        # Save the image as a temporary PNG file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            output_path = temp_file.name
            final_image.save(output_path, "PNG")

        return output_path
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return None

# Function to convert PNG to JPG
def convert_to_jpg(png_path):
    try:
        with Image.open(png_path) as img:
            jpg_path = png_path.replace(".png", ".jpg")
            img.convert("RGB").save(jpg_path, "JPEG")
        return jpg_path
    except Exception as e:
        logger.error(f"Error converting PNG to JPG: {e}")
        return None

# Handle the callback query (button click responses)
@app.on_callback_query()
async def callback_handler(_, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = await get_user_data(user_id)  # Replace with your method to retrieve user data

    # If no photo is uploaded yet, prompt user to upload a photo first
    if not user_data or not user_data.get("photo_path"):
        await callback_query.answer("Please upload a photo first.", show_alert=True)
        return

    # Handle button presses and update user data accordingly
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
    elif callback_query.data == "blur_decrease":
        user_data['blur_radius'] = max(user_data['blur_radius'] - 1, 0)
    elif callback_query.data == "blur_increase":
        user_data['blur_radius'] += 1
    elif callback_query.data == "font_deadly_advance_italic":
        user_data['font'] = "fonts/Deadly Advance Italic (1).ttf"
    elif callback_query.data == "font_deadly_advance":
        user_data['font'] = "fonts/Deadly Advance.ttf"
    elif callback_query.data == "font_trick_or_treats":
        user_data['font'] = "fonts/Trick or Treats.ttf"
    elif callback_query.data == "font_vampire_wars_italic":
        user_data['font'] = "fonts/Vampire Wars Italic.ttf"
    elif callback_query.data == "font_lobster":
        user_data['font'] = "fonts/FIGHTBACK.ttf"
    elif callback_query.data == "download_jpg":
        # Convert final image to JPG
        final_image_path = await add_text_to_image(user_data['photo_path'], user_data['text'], user_data['font'], user_data['text_position'], user_data['size_multiplier'], user_data['text_color'], user_data['blur_radius'])
        
        if final_image_path:
            # Convert to JPG
            jpg_path = convert_to_jpg(final_image_path)
            if jpg_path:
                with open(jpg_path, "rb") as jpg_file:
                    await callback_query.message.reply_document(jpg_file, caption="Here is your logo as a JPG file.")
                os.remove(jpg_path)  # Clean up the temporary JPG file after sending it
                os.remove(final_image_path)  # Clean up the temporary PNG file after sending it
            else:
                await callback_query.message.reply_text("Error converting image to JPG.")
        else:
            await callback_query.message.reply_text("Error generating the final logo.")

        return

    # Save the updated user data
    await save_user_data(user_id, user_data)

    # Regenerate the logo with the new adjustments
    font_path = user_data.get("font", "fonts/Deadly Advance.ttf")
    output_path = await add_text_to_image(user_data['photo_path'], user_data['text'], font_path, user_data['text_position'], user_data['size_multiplier'], user_data['text_color'], user_data['blur_radius'])

    if output_path is None:
        await callback_query.message.reply_text("There was an error generating the logo. Please try again.")
        return

    # Update the image with the new adjustments
    await callback_query.message.edit_media(InputMediaPhoto(media=output_path, caption="Here is your logo with the changes!"), reply_markup=get_adjustment_keyboard())
    await callback_query.answer()  # Acknowledge the callback


# Initialize the Pyrogram Client (this is required for the bot)
app = Client(
    "logo_creator_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# Start the bot
if __name__ == "__main__":
    app.run()
    
