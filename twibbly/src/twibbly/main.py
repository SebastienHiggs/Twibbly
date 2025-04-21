import os
import platform
import logging
import tempfile
import asyncio
from dotenv import load_dotenv
from supabase import acreate_client, AClient
from PIL import Image, ImageDraw, ImageFont

class Printer:
    def __init__(self, label_width_mm=100, label_height_mm=50, dpi=203):
        # 🪵 Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        self.dpi = dpi
        self.set_label_size_mm(label_width_mm, label_height_mm)

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

    def set_label_size_mm(self, width_mm, height_mm):
        """Set label size in millimeters and convert to pixels internally."""
        self.label_width = int((width_mm / 25.4) * self.dpi)
        self.label_height = int((height_mm / 25.4) * self.dpi)
        self.logger.info(f"Label size set to {width_mm}x{height_mm} mm ({self.label_width}x{self.label_height} px)")


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
        width = self.label_width
        height = self.label_height
        try:
            self.logger.debug(f"Generating label image for: {first_name} {last_name} ({width}x{height})")
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)

            # Scale fonts proportionally
            try:
                font_large = ImageFont.truetype("arial.ttf", int(height * 0.25))  # ~25% of height
                font_small = ImageFont.truetype("arial.ttf", int(height * 0.15))  # ~15% of height
            except IOError:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw.text((width // 2, int(height * 0.35)), first_name, font=font_large, fill='black', anchor="mm")
            draw.text((width // 2, int(height * 0.7)), last_name, font=font_small, fill='black', anchor="mm")

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
    def __init__(self, supabase, session_id):
        self.supabase = supabase
        self.SESSION_ID = session_id
        self.setup_printer()
    
    def setup_printer(self):
        self.printer = Printer()
        self.printer.select_printer(printer_name='DYMO LabelWriter 450')

    @classmethod
    async def create(cls):
        load_dotenv()
        SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        SESSION_ID = os.getenv("SESSION_ID")

        if not all([SUPABASE_URL, SUPABASE_KEY, SESSION_ID]):
            raise RuntimeError("Missing required environment variables")

        supabase = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
        return cls(supabase, SESSION_ID)

    async def handle_insert_async(self, payload):
        data = payload["data"]
        record = data["record"]
        first_name = record["first_name"]
        last_name = record["last_name"]
        row_id = record["id"]
        # if new_row["session_id"] != self.SESSION_ID:
        #     return
        print(f"🖨️ Got new row: {first_name} {last_name}")
        self.printer.print_name(first_name=first_name, last_name=last_name)
        await self.supabase.table("name_entries").update({"printed": True}).eq("id", row_id).execute()

    def handle_insert(self, payload):
        asyncio.create_task(self.handle_insert_async(payload))

    async def main(self):
        await self.supabase.realtime.connect()
        await (
            self.supabase.realtime
            .channel("name_entries_channel")
            .on_postgres_changes("INSERT", schema="public", table="name_entries", callback=self.handle_insert)
            .subscribe()
        )

        print("🔔 Listening for new name entries...")
        await self.supabase.realtime.listen()
        await asyncio.sleep(300)

async def async_main():
    twib = await Twibbly.create()
    await twib.main()

if __name__ == "__main__":
    # asyncio.run(async_main())
    printer = Printer()
    printer.select_printer(printer_name='DYMO LabelWriter 450')
    printer.print_name("Mee", "Youu")