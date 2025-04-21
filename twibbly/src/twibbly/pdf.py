import os
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, mm
import win32print

SUMATRA_PATH = r"C:\Users\Sebastien\AppData\Local\SumatraPDF\SumatraPDF.exe"  # Update if installed elsewhere
LABEL_FILENAME = "label.pdf"

def generate_pdf_label(first_name, last_name, filename=LABEL_FILENAME):
    label_width_mm = 36
    label_height_mm = 89
    page_width = label_width_mm * mm
    page_height = label_height_mm * mm

    c = canvas.Canvas(filename, pagesize=(page_width, page_height))

    # Rotate to draw horizontally on vertical label
    c.translate(0, page_height)
    c.rotate(-90)

    label_width = page_height  # 89 mm
    label_height = page_width  # 36 mm

    # 🔲 Outer border: actual label size (for debugging)
    c.setLineWidth(0.5)
    c.setStrokeGray(0.75)  # Light grey outline for debugging
    c.rect(0, 0, label_width, label_height)

    margin = 15

    # 📏 Safe margin box (~3mm padding)
    margin_x = margin * mm
    margin_y = margin * mm
    safe_x = margin_x
    safe_y = margin_y
    safe_width = label_width - 2 * margin_x
    safe_height = label_height - 2 * margin_y

    c.setStrokeGray(0)  # black
    c.setLineWidth(1)
    c.rect(0, 0, safe_width, safe_height)

    # 🖋 Text centered in safe zone
    center_x = label_width / 2
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(center_x, safe_y + safe_height * 0.65, first_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(center_x, safe_y + safe_height * 0.35, last_name)

    c.showPage()
    c.save()
    print(f"✅ PDF label with margins saved to: {os.path.abspath(filename)}")


def get_printers():
    return [printer[2] for printer in win32print.EnumPrinters(2)]

def print_with_sumatra(filename=LABEL_FILENAME, printer_name=None):
    if not printer_name:
        printer_name = win32print.GetDefaultPrinter()

    abs_path = os.path.abspath(filename)
    print(f"🖨️ Printing '{abs_path}' to printer: {printer_name}")

    command = f'"{SUMATRA_PATH}" -print-to "{printer_name}" -silent "{abs_path}"'
    try:
        # Use shell=True to run like CMD does
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        if result.returncode == 0:
            print("✅ Print job sent successfully.")
        else:
            print(f"❌ Print failed with return code {result.returncode}")
    except Exception as e:
        print(f"❌ Exception while printing: {e}")

if __name__ == "__main__":
    print("📋 Available printers:")
    for p in get_printers():
        print(" -", p)

    generate_pdf_label("John", "Doe")
    print_with_sumatra()