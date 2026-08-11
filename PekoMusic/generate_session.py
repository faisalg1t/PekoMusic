"""
Run this once to generate STRING_SESSION for your assistant (userbot) account.

    python3 -m PekoMusic.generate_session

You will be asked to log in with the phone number of the account you want
to use as the music-streaming assistant. NEVER share the resulting string —
it grants full access to that Telegram account.
"""

from pyrogram import Client

API_ID = int(input("Enter your API_ID: ").strip())
API_HASH = input("Enter your API_HASH: ").strip()

with Client(name="peko_session_gen", api_id=API_ID, api_hash=API_HASH, in_memory=True) as app:
    session_string = app.export_session_string()
    print("\n\nYour STRING_SESSION (keep this secret!):\n")
    print(session_string)
    print("\nPaste this into your .env file as STRING_SESSION=...\n")
