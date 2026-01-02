import os
import time

import requests
from telegram.client import Telegram


class TelegramBotError(Exception):
    """Base exception for Telegram bot operations"""


class MessageNotFoundError(TelegramBotError):
    """Raised when no messages are found in the chat"""


class ButtonNotFoundError(TelegramBotError):
    """Raised when a button is not found in a message"""


class UnexpectedMessageError(TelegramBotError):
    """Raised when an unexpected message is received"""


class ButtonClickError(TelegramBotError):
    """Raised when clicking a button fails"""


def get_cred(env_var_name: str, required: bool = True) -> str | None:
    env_value = os.environ.get(env_var_name)
    if required and not env_value:
        raise ValueError(f'env var "{env_var_name}" is required')

    return env_value


# credentials from https://my.telegram.org
API_ID = get_cred("API_ID")
API_HASH = get_cred("API_HASH")
PHONE_NUMBER = get_cred("PHONE_NUMBER")
DATABASE_ENCRYPTION_KEY = get_cred("DATABASE_ENCRYPTION_KEY")
ALFAMEDOBOT_CHAT_ID = int(get_cred("ALFAMEDOBOT_CHAT_ID"))
TD_LIBRARY_PATH = get_cred("TD_LIBRARY_PATH", required=False)

# Telegram notification settings
TG_NOTIFICATION_CHAT_ID = get_cred("TG_NOTIFICATION_CHAT_ID")
TG_NOTIFICATION_BOT_TOKEN = get_cred("TG_NOTIFICATION_BOT_TOKEN")

KNOWN_CLINICS = [
    "АВС-Медицина (м.Парк Культуры)",
    "Медси (м.Марьино)",
    "Медси (м.Полянка)",
    "Медси (м.Шаболовская)",
]


def send_telegram_notification(message: str) -> bool:
    url = f"https://api.telegram.org/bot5214201125:{TG_NOTIFICATION_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_NOTIFICATION_CHAT_ID, "text": message}

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✓ Telegram notification sent successfully")


def get_latest_message(tg: Telegram, chat_id: int) -> dict:
    result = tg.get_chat_history(chat_id=chat_id, limit=1)
    result.wait()

    if result.error:
        raise TelegramBotError(f"Error fetching messages: {result.error_info}")

    messages = result.update.get("messages", [])

    if len(messages) == 0:
        raise MessageNotFoundError("No messages found in chat")

    return messages[0]


def check_message_text(message: dict, expected_text: str) -> bool:
    """Check if message contains expected text"""
    content = message.get("content", {})
    if content.get("@type") != "messageText":
        return False

    text = content.get("text", {}).get("text", "")
    return expected_text in text


def find_button(message: dict, button_text: str) -> tuple[int, int, dict]:
    """
    Find a button with specific text in message's inline keyboard.

    Returns:
        tuple: (row_idx, button_idx, button)

    Raises:
        ButtonNotFoundError: If the button is not found
    """
    reply_markup = message.get("reply_markup")

    if not reply_markup or reply_markup.get("@type") != "replyMarkupInlineKeyboard":
        raise ButtonNotFoundError(
            f"Button '{button_text}' not found: no inline keyboard in message"
        )

    rows = reply_markup.get("rows", [])
    for row_idx, row in enumerate(rows):
        for button_idx, button in enumerate(row):
            if button_text in button.get("text", ""):
                return row_idx, button_idx, button

    raise ButtonNotFoundError(f"Button '{button_text}' not found in message")


def click_button(tg: Telegram, chat_id: int, message_id: int, button: dict) -> None:
    """
    Click an inline keyboard button.

    Raises:
        ButtonClickError: If clicking the button fails
    """
    button_type = button.get("type", {})
    callback_data = button_type.get("data", "")

    print(f"  Clicking button: {button.get('text')}")

    result = tg.call_method(
        "getCallbackQueryAnswer",
        params={
            "chat_id": chat_id,
            "message_id": message_id,
            "payload": {"@type": "callbackQueryPayloadData", "data": callback_data},
        },
    )
    result.wait()

    if result.error:
        raise ButtonClickError(f"Error clicking button: {result.error_info}")

    print("  ✓ Button clicked successfully")


def extract_clinic_names(message: dict) -> list[str]:
    """Extract all clinic names from the inline keyboard buttons"""
    reply_markup = message.get("reply_markup")

    if not reply_markup or reply_markup.get("@type") != "replyMarkupInlineKeyboard":
        return []

    clinics = []
    rows = reply_markup.get("rows", [])

    for row in rows:
        for button in row:
            button_text = button.get("text", "")
            # Skip navigation buttons (arrows and "back" buttons)
            if button_text.startswith(("⬆", "◀", "⬅")):
                continue
            clinics.append(button_text)

    return clinics


def navigate_and_get_clinics(tg: Telegram, chat_id: int) -> list[str]:
    """
    Navigate through bot menu and get clinic list.

    Args:
        tg: Telegram client instance
        chat_id: Chat ID to interact with

    Returns:
        list: List of clinic names
    """
    print("Step 1: Getting initial message...")
    message = get_latest_message(tg, chat_id)

    # Check if we're already at the clinic selection screen - need to restart
    if check_message_text(message, "ВЫБОР КЛИНИКИ"):
        print("  ✓ Already at clinic selection screen, going back to start...")

        # Find and click "В начало" button to restart
        _, _, button = find_button(message, "В начало")
        click_button(tg, chat_id, message.get("id"), button)

        print("  Waiting for bot response...")
        time.sleep(2)

        # Get the new message (should be welcome screen)
        message = get_latest_message(tg, chat_id)

    # Step 2: Check if it's the welcome message and click "Записаться"
    if check_message_text(message, "ДОБРО ПОЖАЛОВАТЬ"):
        print("  ✓ Found welcome message: 'ДОБРО ПОЖАЛОВАТЬ!'")

        _, _, button = find_button(message, "Записаться")
        click_button(tg, chat_id, message.get("id"), button)

        print("  Waiting for bot response...")
        time.sleep(2)

        # Get the new message
        message = get_latest_message(tg, chat_id)

    # Step 3: Check if it's the scenario selection message and click "Выбрать клинику"
    print("\nStep 2: Checking for scenario selection message...")
    if not check_message_text(message, "ВЫБОР СЦЕНАРИЯ ЗАПИСИ"):
        msg_text = message.get("content", {}).get("text", {}).get("text", "N/A")[:100]
        raise UnexpectedMessageError(
            f"Expected message with 'ВЫБОР СЦЕНАРИЯ ЗАПИСИ', got: {msg_text}"
        )

    print("  ✓ Found scenario selection message: 'ВЫБОР СЦЕНАРИЯ ЗАПИСИ'")

    _, _, button = find_button(message, "Выбрать клинику")
    click_button(tg, chat_id, message.get("id"), button)

    print("  Waiting for bot response...")
    time.sleep(2)

    print("\nStep 3: Getting clinic list...")
    message = get_latest_message(tg, chat_id)

    clinics = extract_clinic_names(message)
    if not clinics:
        raise TelegramBotError("No clinics found in the message")

    return clinics


def get_new_clinics() -> list[str]:
    """initialize client, get clinics, cleanup"""
    tg = Telegram(
        api_id=API_ID,
        api_hash=API_HASH,
        phone=PHONE_NUMBER,
        database_encryption_key=DATABASE_ENCRYPTION_KEY,
        files_directory="tdlib_files/",
        library_path=TD_LIBRARY_PATH,
    )

    try:
        tg.login()
        print("✓ Logged in successfully!\n")

        clinics = navigate_and_get_clinics(tg, ALFAMEDOBOT_CHAT_ID)

        new_clinics = [clinic for clinic in clinics if clinic not in KNOWN_CLINICS]

        print(f"✓ Found {len(clinics)} clinics:")

        for idx, clinic_name in enumerate(clinics, 1):
            print(f"{idx}. {clinic_name}")

        return new_clinics
    finally:
        tg.stop()


if __name__ == "__main__":
    while True:
        print(f"\n{'=' * 60}")

        try:
            new_clinics = get_new_clinics()
        except Exception as e:
            error_msg = f"Clinic Check Error: Unexpected error: {e}"
            print(f"\n✗ {error_msg}")
            send_telegram_notification(error_msg)
            new_clinics = []

        if new_clinics:
            notify_msg = f"⚠️ NEW CLINICS DETECTED: {', '.join(new_clinics)}"

            print(notify_msg)
            send_telegram_notification(notify_msg)

        time.sleep(60 * 60 * 3)
