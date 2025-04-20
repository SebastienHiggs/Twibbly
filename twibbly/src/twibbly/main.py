import time
import os
import platform
import logging
import tempfile
from dotenv import load_dotenv
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont

# OS-specific printing
try:
    import win32print
    import win32api
except ImportError:
    win32print = None

try:
    import cups
except ImportError:
    cups = None

# 🪵 Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 🔐 Load secrets from .env
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
SESSION_ID = os.getenv("SESSION_ID")

if not all([SUPABASE_URL, SUPABASE_KEY, SESSION_ID]):
    logger.critical("Missing environment variables in .env file. Exiting.")
    raise RuntimeError("Missing environment variables in .env")

logger.info("Environment variables loaded successfully.")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info("Supabase client initialized.")

def generate_label_image(first_name, last_name) -> str:
    try:
        logger.debug(f"Generating label image for: {first_name} {last_name}")
        image = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(image)
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 24)

        draw.text((200, 60), first_name, font=font_large, fill='black', anchor="mm")
        draw.text((200, 130), last_name, font=font_small, fill='black', anchor="mm")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image.save(temp_file.name)
        logger.info(f"Label image saved to {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logger.exception("Failed to generate label image")
        raise

def print_file(filepath: str):
    system = platform.system()
    try:
        logger.info(f"Attempting to print on {system}...")
        if system == "Windows" and win32print:
            printer_name = win32print.GetDefaultPrinter()
            hprinter = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(hprinter, 2)
            win32print.ClosePrinter(hprinter)

            logger.info(f"Sending to printer: {printer_name}")
            win32api.ShellExecute(0, "print", filepath, None, ".", 0)

        elif system in {"Linux", "Darwin"} and cups:
            conn = cups.Connection()
            printer_name = conn.getDefault()
            logger.info(f"Sending to printer: {printer_name}")
            conn.printFile(printer_name, filepath, "Nametag", {})

        else:
            raise EnvironmentError("No compatible printing method found on this system.")
    except Exception as e:
        logger.exception("Printing failed")

def loop_code(printed_ids):
    response = supabase.from_("name_entries") \
                .select("id, first_name, last_name") \
                .eq("session_id", SESSION_ID) \
                .order("created_at", desc=False) \
                .execute()
            
    if not response.data:
        logger.debug("No new entries found.")
        return

    for row in response.data:
        row_id = row["id"]
        if row_id not in printed_ids:
            full_name = f"{row['first_name']} {row['last_name']}"
            logger.info(f"Processing new name entry: {full_name}")
            filepath = generate_label_image(row["first_name"], row["last_name"])
            print_file(filepath)
            time.sleep(3)
            printed_ids.add(row_id)

def main():
    logger.info("Starting main loop...")
    printed_ids = set()
    while True:
        try:
            loop_code(printed_ids)
        except Exception as e:
            logger.exception("Error during polling loop")
        time.sleep(2)

if __name__ == "__main__":
    main()
