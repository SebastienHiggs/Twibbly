import os
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import win32print

SUMATRA_PATH = r"C:\Users\Sebastien\AppData\Local\SumatraPDF\SumatraPDF.exe"  # Change if needed

class LabelPrinter:
    def __init__(self, width_mm=52, height_mm=60, margin_mm=3, printer_name=None):
        self.label_width_mm = width_mm
        self.label_height_mm = height_mm
        self.margin_mm = margin_mm
        self.label_filename = "label.pdf"
        self.printer_name = printer_name or win32print.GetDefaultPrinter()

    def generate_label(self, first_name, last_name):
        page_width = self.label_width_mm * mm
        page_height = self.label_height_mm * mm
        margin = self.margin_mm * mm

        c = canvas.Canvas(self.label_filename, pagesize=(page_width, page_height))
        c.translate(0, page_height)
        c.rotate(-90)

        label_width = page_height
        label_height = page_width

        # Full label boundary
        c.setStrokeGray(0.75)
        c.setLineWidth(0.5)
        c.rect(0, 0, label_width, label_height)

        # Safe margin box
        safe_x = margin
        safe_y = margin
        safe_width = label_width - 2 * margin
        safe_height = label_height - 2 * margin

        c.setStrokeGray(0)
        c.setLineWidth(1)
        c.rect(safe_x, safe_y, safe_width, safe_height)

        # Centered text
        center_x = label_width / 2
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(center_x, safe_y + safe_height * 0.65, first_name)

        c.setFont("Helvetica", 14)
        c.drawCentredString(center_x, safe_y + safe_height * 0.35, last_name)

        c.showPage()
        c.save()

        print(f"✅ Label PDF saved: {os.path.abspath(self.label_filename)}")

    def print_label(self):
        abs_path = os.path.abspath(self.label_filename)
        print(f"🖨️ Printing '{abs_path}' to printer: {self.printer_name}")

        command = f'"{SUMATRA_PATH}" -print-to "{self.printer_name}" -silent "{abs_path}"'
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
            if result.returncode == 0:
                print("✅ Print job sent successfully.")
            else:
                print(f"❌ Print failed with return code {result.returncode}")
        except Exception as e:
            print(f"❌ Exception while printing: {e}")

    @staticmethod
    def list_printers():
        return [printer[2] for printer in win32print.EnumPrinters(2)]


if __name__ == "__main__":
    print("📋 Available printers:")
    for p in LabelPrinter.list_printers():
        print(" -", p)

    printer = LabelPrinter(width_mm=52, height_mm=60)
    printer.generate_label("John", "Doe")
    printer.print_label()
