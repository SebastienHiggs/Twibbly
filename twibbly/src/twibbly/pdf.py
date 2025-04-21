import os
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, mm
import win32print

SUMATRA_PATH = r"C:\Users\Sebastien\AppData\Local\SumatraPDF\SumatraPDF.exe"  # Update if installed elsewhere
LABEL_FILENAME = "label.pdf"

def generate_pdf_label(first_name, last_name, filename=LABEL_FILENAME):
    # Physical label size: 36mm (width) x 89mm (height)
    label_width_mm = 36
    label_height_mm = 89
    page_width = label_width_mm * mm
    page_height = label_height_mm * mm

    c = canvas.Canvas(filename, pagesize=(page_width, page_height))

    # Rotate the canvas to write horizontal text on vertical label
    c.translate(0, page_height)  # Move origin to top-left
    c.rotate(-90)  # Rotate clockwise

    # Now draw text on a virtual 89mm x 36mm landscape layout
    label_width = page_height
    label_height = page_width

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(label_width / 2, label_height * 0.65, first_name)

    c.setFont("Helvetica", 16)
    c.drawCentredString(label_width / 2, label_height * 0.35, last_name)

    c.showPage()
    c.save()
    print(f"✅ PDF label generated at: {os.path.abspath(filename)}")

def get_printers():
    return [printer[2] for printer in win32print.EnumPrinters(2)]

def print_with_sumatra(filename=LABEL_FILENAME, printer_name=None):
    if not printer_name:
        printer_name = win32print.GetDefaultPrinter()

    abs_path = os.path.abspath(filename)
    print(f"🖨️ Printing '{abs_path}' to printer: {printer_name}")

    try:
        subprocess.run([
            SUMATRA_PATH,
            "-print-to", printer_name,
            "-silent",
            abs_path
        ], check=True)
        print("✅ Print job sent successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Print failed: {e}")
    except FileNotFoundError:
        print(f"❌ SumatraPDF not found at: {SUMATRA_PATH}")

if __name__ == "__main__":
    print("📋 Available printers:")
    for p in get_printers():
        print(" -", p)

    generate_pdf_label("John", "Doe")
    print_with_sumatra()