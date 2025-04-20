import time
import os
import platform
import logging
import tempfile
from dotenv import load_dotenv
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont

class Printer:
    def __init__(self):
        # 🪵 Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        self.selected_printer = None

        self.label_image_path = None
        self.os_type = platform.system()

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
            self.logger.warning("win32print or win32api not available.")
            self.win32print = None
            self.win32api = None

    def _init_linux(self):
        try:
            import cups
            self.cups = cups
        except ImportError:
            self.logger.warning("cups not available.")
            self.cups = None

    def print_name(self, first_name, last_name):
        self._generate_label_image(first_name, last_name)

        if not self.label_image_path:
            self.logger.error("Failed to generate label image file.")
            return

        try:
            if self.os_type == "Windows" and self.win32print:
                self._print_image_windows()
            elif self.os_type == "Linux" and self.cups:
                self._print_image_linux()
            else:
                self.logger.error("No supported printing backend available.")
            return True
        finally:
            # Clean up the temp file
            if self.label_image_path and os.path.exists(self.label_image_path):
                os.remove(self.label_image_path)
                self.logger.debug(f"Deleted temp file {self.label_image_path}")
            self.label_image_path = None
            return False

    def _generate_label_image(self, first_name, last_name):
        try:
            self.logger.debug(f"Generating label image for: {first_name} {last_name}")
            image = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(image)

            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except IOError:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw.text((200, 60), first_name, font=font_large, fill='black', anchor="mm")
            draw.text((200, 130), last_name, font=font_small, fill='black', anchor="mm")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp:
                image.save(temp.name)
                self.label_image_path = temp.name
                self.logger.info(f"Label image saved to {self.label_image_path}")
        except Exception:
            self.logger.exception("Failed to generate label image")
            raise

    def _print_image_windows(self):
        try:
            import win32ui
            from PIL import ImageWin

            printer_name = self.selected_printer or self.win32print.GetDefaultPrinter()
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Nametag")
            hdc.StartPage()

            img = Image.open(self.label_image_path)
            dib = ImageWin.Dib(img)
            dib.draw(hdc.GetHandleOutput(), (0, 0, img.width, img.height))

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()
            self.logger.info("Printed label image on Windows.")
        except Exception:
            self.logger.exception("Failed to print image on Windows")

    def _print_image_linux(self):
        try:
            conn = self.cups.Connection()
            printer_name = self.selected_printer or conn.getDefault()
            conn.printFile(printer_name, self.label_image_path, "Nametag", {})
            self.logger.info(f"Printed to {printer_name} on Linux.")
        except Exception:
            self.logger.exception("Failed to print image on Linux")

    def list_printers(self):
        try:
            if self.os_type == "Windows" and self.win32print:
                printers = [printer[2] for printer in self.win32print.EnumPrinters(2)]
            elif self.os_type == "Linux" and self.cups:
                conn = self.cups.Connection()
                printers = list(conn.getPrinters().keys())
            else:
                raise EnvironmentError("Printer listing not supported on this OS.")
            self.logger.info(f"Available printers: {printers}")
            return printers
        except Exception:
            self.logger.exception("Failed to list printers.")
            return []
        
    def select_printer(self, printer_name):
        printers = self.list_printers()
        if printer_name in printers:
            self.selected_printer = printer_name
            self.logger.info(f"Selected printer: {printer_name}")
        else:
            self.logger.warning(f"Printer '{printer_name}' not found. Available: {printers}")
            self.selected_printer = None


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

        # session_exists = self.supabase.from_("sessions").select("id").eq("id", self.SESSION_ID).maybe_single().execute()
        # if not session_exists.data:
        #     self.logger.warning(f"Session ID {self.SESSION_ID} does not exist in 'sessions' table.")

        self.printer = Printer()
        self.printer.select_printer(printer_name='DYMO LabelWriter 450')

    def get_updated_table(self):
        response = self.supabase.from_("name_entries") \
                        .select("id, first_name, last_name, printed") \
                        .eq("session_id", self.SESSION_ID) \
                        .order("created_at", desc=False) \
                        .execute()
        return response
    
    def set_row_printed_true(self, row):
        self.supabase.from_("name_entries") \
            .update({"printed": True}) \
            .eq("id", row["id"]) \
            .execute()

    def loop_code(self):
        response = self.get_updated_table()
                
        if not response.data:
            self.logger.debug("No new entries found.")
            return

        for row in response.data:
            if not row["printed"]:
                self.logger.info(f"Processing new name entry: {row['first_name']} {row['last_name']}")
                print_success = self.printer.print_name(first_name=row['first_name'], last_name=row['last_name'])
                if print_success:
                    self.set_row_printed_true(row)
                    input()

    def main(self):
        self.logger.info("Starting main loop...")

        while True:
            try:
                self.loop_code()
            except KeyboardInterrupt:
                self.logger.info("Shutting down gracefully.")
            except Exception as e:
                self.logger.exception("Error during polling loop")
            time.sleep(2)

if __name__ == "__main__":
    twibbly = Twibbly()
    twibbly.loop_code()
