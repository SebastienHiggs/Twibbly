import os
import platform
import logging
import asyncio
from dotenv import load_dotenv
from supabase import acreate_client, AClient
from .pdf import LabelPrinter


class Twibbly:
    def __init__(self, supabase: AClient, session_id: str):
        self.supabase = supabase
        self.SESSION_ID = session_id
        self.setup_printer()

    def setup_printer(self):
        # Adjust label dimensions here if needed
        self.printer = LabelPrinter(
            width_mm=52,
            height_mm=60,
            printer_name="DYMO LabelWriter 450"
        )

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

        print(f"🖨️ Got new row: {first_name} {last_name}")
        preview_only = None
        # preview_only = True # Comment out for printing
        if preview_only is True:
            self.printer.generate_label(first_name, last_name)
            self.printer.print_label()

        await self.supabase.table("name_entries") \
            .update({"printed": True}) \
            .eq("id", row_id) \
            .execute()

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
    # For testing single print manually
    printer = LabelPrinter(width_mm=52, height_mm=60, printer_name="DYMO LabelWriter 450")
    printer.generate_label("Mee", "Youu")
    printer.print_label()
