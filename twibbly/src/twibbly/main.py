import time
import os
import platform
from dotenv import load_dotenv
from supabase import create_client, Client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# 🔐 Load secrets from .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SESSION_ID = os.getenv("SESSION_ID")

if not all([SUPABASE_URL, SUPABASE_KEY, SESSION_ID]):
    raise RuntimeError("Missing environment variables in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_label(first_name, last_name, filename="label.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(300, 500, first_name)
    c.setFont("Helvetica", 24)
    c.drawCentredString(300, 450, last_name)
    c.save()

def print_file(filepath):
    system = platform.system()
    if system == "Windows":
        print("Sending to printer via os.startfile...")
        os.startfile(filepath, "print")
    elif system == "Darwin" or system == "Linux":
        os.system(f"lp {filepath}")
    else:
        print(f"Unsupported OS for printing: {system}")

def main():
    printed_ids = set()
    while True:
        try:
            response = supabase.from_("name_entries") \
                .select("id, first_name, last_name") \
                .eq("session_id", SESSION_ID) \
                .order("created_at", desc=False) \
                .execute()

            for row in response.data:
                row_id = row["id"]
                if row_id not in printed_ids:
                    print(f"Printing: {row['first_name']} {row['last_name']}")
                    generate_label(row["first_name"], row["last_name"])
                    print_file("label.pdf")
                    time.sleep(3)  # give time for print job to start
                    printed_ids.add(row_id)

        except Exception as e:
            print(f"Error during loop: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
