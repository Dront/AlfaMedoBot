# @AlfaMedoBot avalable clinics monitor

This project uses TDLib (Telegram Database Library) to login to your Telegram account and alert you on telegram when new clinic is found in @AlfaMedoBot. Primarily to find out when Чайка will become available :)

Script will:
- Run every 3 hours
- Login with your phone number to your tg account
- Talk to the @AlfaMedoBot (Айболибот) and parse its available clinics list
- Send tg message and log alert when new unknown clinics are detected
- Send and log errors if the script fails

Known clinics (alerts are sent when any other clinic is found):
1. АВС-Медицина (м.Парк Культуры)
2. Медси (м.Марьино)
3. Медси (м.Полянка)
4. Медси (м.Шаболовская)


## Installation

### Option 1: Docker

Docker provides an isolated environment and handles all dependencies automatically.

1. Make sure Docker is installed on your system
2. Edit sample configuration in `local.env`
3. Build and run:
```bash
docker build -t alfamedobot .
docker run -it -v ./tdlib_files:/tdlib_files --env-file local.env alfamedobot
```

The session data will be persisted in the `tdlib_files/` directory on your host machine after the first login.

### Option 2: Local Environment

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```
2. Edit sample configuration in `local.env`. Apply it.
3. Try to run `python get_clinics_list.py`. If there is an error about missing library (.so file), compile tdlib with instructions from https://tdlib.github.io/td/build.html?language=Python, and try again. Instructions for compiling on debian are provided in the `Dockerfile`.

## Configuration

```bash
# Get these credentials from https://my.telegram.org
API_ID=1234567
API_HASH=123qweasd
# Your tg account phone number. App will use it as a login to tg account.
PHONE_NUMBER=+79031234567
# Any random string. Should be the same on the same database path.
DATABASE_ENCRYPTION_KEY=randomstring
# Tg chat id of @AlfaMedoBot. You have /start the bot in your normal tg client, and find out bot's chat id.
ALFAMEDOBOT_CHAT_ID=7509713245
# Chat id of your bot. You have to create a bot via @BotFather, /start it in your normal tg client, and find out bot's chat id. Notifications of new clinics and errors will be went there.
TG_NOTIFICATION_CHAT_ID=12355765
# Tg token of your bot. Messages about new clinics will be used via this token. @BotFather shows this token on bot creation.
TG_NOTIFICATION_BOT_TOKEN=123456:qweasd123
```

## Usage

**First time login:**
- You'll receive a code on your Telegram app
- Enter the code when prompted
- If you have 2FA enabled, enter your password

**Subsequent runs:**
- The session will be saved in `tdlib_files/` directory
- You won't need to login again unless you remove this folder
