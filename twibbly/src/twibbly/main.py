import time
import os
import platform
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# 🪵 Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
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

def generate_label(first_name, last_name, filename="label.pdf"):
    try:
        logger.debug(f"Generating label PDF for: {first_name} {last_name}")
        c = canvas.Canvas(filename, pagesize=letter)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(300, 500, first_name)
        c.setFont("Helvetica", 24)
        c.drawCentredString(300, 450, last_name)
        c.save()
        logger.info(f"Label generated and saved to {filename}")
    except Exception as e:
        logger.exception(f"Failed to generate label: {e}")

def print_file(filepath):
    system = platform.system()
    try:
        if system == "Windows":
            logger.info("Printing via os.startfile on Windows...")
            os.startfile(filepath, "print")
        elif system in {"Darwin", "Linux"}:
            logger.info(f"Printing via 'lp' on {system}...")
            os.system(f"lp {filepath}")
        else:
            logger.error(f"Unsupported OS for printing: {system}")
    except Exception as e:
        logger.exception(f"Print command failed: {e}")

def main():
    logger.info("Starting main loop...")
    printed_ids = set()
    while True:
        try:
            response = supabase.from_("name_entries") \
                .select("id, first_name, last_name") \
                .eq("session_id", SESSION_ID) \
                .order("created_at", desc=False) \
                .execute()

            if not response.data:
                logger.debug("No new entries found.")

            for row in response.data:
                row_id = row["id"]
                if row_id not in printed_ids:
                    full_name = f"{row['first_name']} {row['last_name']}"
                    logger.info(f"Processing new name entry: {full_name}")
                    generate_label(row["first_name"], row["last_name"])
                    print_file("label.pdf")
                    time.sleep(3)  # let the print job spool
                    printed_ids.add(row_id)

        except Exception as e:
            logger.exception("Error during polling loop")
        time.sleep(2)

if __name__ == "__main__":
    main()
