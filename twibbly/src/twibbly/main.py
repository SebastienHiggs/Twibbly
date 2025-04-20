import time
import os
import platform
import logging
import tempfile
from dotenv import load_dotenv
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont

class Printer():
    def __init__(self):
        # 🪵 Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        if self.os_type == "Windows":
            self._init_windows()
        elif self.os_type == "Linux":
            self._init_linux()
        else:
            self.logger.warning(f"Unsupported OS: {self.os_type}")

    def _init_windows(self):
        try:
            import win32print, win32api
            self.win32print = win32print
            self.win32api = win32api
        except ImportError:
            print("[WARN] win32print or win32api not available.")

    def _init_linux(self):
        try:
            import cups
            self.cups = cups
        except ImportError:
            print("[WARN] cups not available.")

    def print_name(self, first_name, last_name):
        pass

    def generate_label_image(self, first_name, last_name) -> str:
        try:
            self.logger.debug(f"Generating label image for: {first_name} {last_name}")
            image = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(image)
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)

            draw.text((200, 60), first_name, font=font_large, fill='black', anchor="mm")
            draw.text((200, 130), last_name, font=font_small, fill='black', anchor="mm")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_file.name)
            self.logger.info(f"Label image saved to {temp_file.name}")
            return temp_file.name
        except Exception as e:
            self.logger.exception("Failed to generate label image")
            raise

    def print_file(self, filepath: str):
        system = platform.system()
        try:
            self.logger.info(f"Attempting to print on {system}...")

            if system == "Windows" and win32print:
                import win32ui
                from PIL import ImageWin, Image

                printer_name = win32print.GetDefaultPrinter()
                hdc = win32ui.CreateDC()
                hdc.CreatePrinterDC(printer_name)
                hdc.StartDoc("Nametag")
                hdc.StartPage()

                img = Image.open(filepath)
                dib = ImageWin.Dib(img)
                # Define printable rectangle — (left, top, right, bottom)
                dib.draw(hdc.GetHandleOutput(), (0, 0, img.width, img.height))

                hdc.EndPage()
                hdc.EndDoc()
                hdc.DeleteDC()
                self.logger.info("Printed to default Windows printer silently.")

            elif system in {"Linux", "Darwin"} and cups:
                conn = cups.Connection()
                printer_name = conn.getDefault()
                conn.printFile(printer_name, filepath, "Nametag", {})
                self.logger.info(f"Printed to {printer_name} on Unix-like OS.")
            else:
                raise EnvironmentError("No compatible printing method found.")
        except Exception as e:
            self.logger.exception("Printing failed")


class Twibbly():
    def __init__(self):
        # 🪵 Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        # 🔐 Load secrets from .env
        load_dotenv()
        self.SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        self.SESSION_ID = os.getenv("SESSION_ID")

        if not all([self.SUPABASE_URL, self.SUPABASE_KEY, self.SESSION_ID]):
            self.logger.critical("Missing environment variables in .env file. Exiting.")
            raise RuntimeError("Missing environment variables in .env")

        self.logger.info("Environment variables loaded successfully.")
        self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
        self.logger.info("Supabase client initialized.")

        self.printer = Printer()

    def loop_code(self, printed_ids = None):
        if printed_ids == None:
            printed_ids = set()

        response = self.supabase.from_("name_entries") \
                    .select("id, first_name, last_name") \
                    .eq("session_id", self.SESSION_ID) \
                    .order("created_at", desc=False) \
                    .execute()
                
        if not response.data:
            self.logger.debug("No new entries found.")
            return

        for row in response.data:
            row_id = row["id"]
            if row_id not in printed_ids:
                full_name = f"{row['first_name']} {row['last_name']}"
                self.logger.info(f"Processing new name entry: {full_name}")
                filepath = self.printer.generate_label_image(row["first_name"], row["last_name"])
                self.printer.print_file(filepath)
                time.sleep(3)
                printed_ids.add(row_id)

    def main(self):
        self.logger.info("Starting main loop...")
        printed_ids = set()
        while True:
            try:
                self.loop_code(printed_ids)
            except Exception as e:
                self.logger.exception("Error during polling loop")
            time.sleep(2)

if __name__ == "__main__":
    # twibbly = Twibbly()
    # twibbly.loop_code()
    # printer = Printer()
    # printer.
    import platform
    print(platform.system())
