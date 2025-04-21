import os
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, mm
import win32print

SUMATRA_PATH = r"C:\Users\Sebastien\AppData\Local\SumatraPDF\SumatraPDF.exe"  # Update if installed elsewhere
LABEL_FILENAME = "label.pdf"

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os

LABEL_FILENAME = "label.pdf"

def generate_pdf_label(first_name, last_name, filename=LABEL_FILENAME):
    # 📐 Exact physical label size in mm
    LABEL_WIDTH_MM = 36 + 16
    LABEL_HEIGHT_MM = 89 - 29
    SAFE_MARGIN_MM = 3  # Padding inside the label, not outside

    # Convert to points (ReportLab uses points)
    page_width = LABEL_WIDTH_MM * mm
    page_height = LABEL_HEIGHT_MM * mm
    margin = SAFE_MARGIN_MM * mm

    # Create a canvas with exact label size
    c = canvas.Canvas(filename, pagesize=(page_width, page_height))

    # 🔄 Rotate so text is horizontal on a vertical label
    c.translate(0, page_height)
    c.rotate(-90)

    # Rotated label width/height
    label_width = page_height  # becomes width after rotation
    label_height = page_width  # becomes height after rotation

    # 🟦 Debug: full label boundary
    c.setStrokeGray(0.75)
    c.setLineWidth(0.5)
    c.rect(0, 0, label_width, label_height)

    # 🔲 Safe print zone inside the label
    safe_x = margin
    safe_y = margin
    safe_width = label_width - 2 * margin
    safe_height = label_height - 2 * margin

    # 🟩 Debug: safe margin zone
    c.setStrokeGray(0)
    c.setLineWidth(1)
    c.rect(safe_x, safe_y, safe_width, safe_height)

    # 🖋 Centered text in safe area
    center_x = label_width / 2
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(center_x, safe_y + safe_height * 0.65, first_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(center_x, safe_y + safe_height * 0.35, last_name)

    c.showPage()
    c.save()

    print(f"✅ Label PDF saved: {os.path.abspath(filename)}")



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