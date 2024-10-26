# Telegram Questionnaire Bot

This project is a Telegram bot that conducts questionnaires and saves responses to Google Sheets. It is built on top of the [python-telegram-bot/examples/pollbot.py](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/pollbot.py) repository, with additional functionality for structured questionnaires and Google Sheets integration.

## Features

- Conducts multi-question surveys with both multiple-choice and open-ended questions
- Saves responses to Google Sheets
- Uses environment variables for secure configuration
- Customizable questionnaire structure

## Prerequisites

- Python 3.7+
- A Telegram Bot Token
- Google Cloud Project with Sheets API enabled
- Google Service Account with access to your Google Sheet

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/easgarli/telegram-questionnaire-bot.git
   cd telegram-questionnaire-bot
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install python-telegram-bot google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv pytz
   ```

## Configuration

### Obtaining a Telegram Bot Token

1. Start a chat with the [BotFather](https://t.me/botfather) on Telegram.
2. Send the command `/newbot` and follow the prompts to create a new bot.
3. Once created, BotFather will give you a token. This is your `BOT_TOKEN`.

### Setting up Google Sheets API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the Google Sheets API for your project.
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name and grant it the "Editor" role for Google Sheets
5. Create a key for the Service Account:
   - In the Service Account details, go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON as the key type
   - Download the key file and rename it to `gsheets-key.json`

### Getting the Spreadsheet ID

1. Create a new Google Sheet or use an existing one.
2. Share the sheet with the email address of your Service Account (found in the `gsheets-key.json` file).
3. The Spreadsheet ID is in the URL of your sheet:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit#gid=0
   ```

### Setting up the .env file

1. Create a `.env` file in the project root and add your Telegram Bot Token and Spreadsheet ID:
   ```
   TEST_BOT_TOKEN=your_bot_token_here
   SPREADSHEET_ID=your_google_sheet_id_here
   ```

2. Place your `gsheets-key.json` file in the project root.

3. Update the `QUESTIONNAIRE` list in `pollbot.py` with your desired questions.

## Customizing the Questionnaire

You can easily modify the questionnaire by editing the `QUESTIONNAIRE` list in `pollbot.py`. Here's how to structure your questions:

```python
QUESTIONNAIRE = [
    {
        "id": "question_id",
        "type": "multiple_choice",
        "question": "Your question here?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"]
    },
    {
        "id": "open_question_id",
        "type": "open_ended",
        "question": "Your open-ended question here:"
    },
    # Add more questions as needed
]
```

- For multiple-choice questions, use `"type": "multiple_choice"` and provide an `"options"` list.
- For open-ended questions, use `"type": "open_ended"`.
- Ensure each question has a unique `"id"` as it will be used as the column header in Google Sheets.

## Usage

1. Run the bot:
   ```
   python pollbot.py
   ```

2. Start a conversation with your bot on Telegram and use the `/start` command to begin the questionnaire.

## Google Sheets Integration

The bot will automatically create a new row in your specified Google Sheet for each completed questionnaire. The sheet will have columns for timestamp, user ID, and each question in your questionnaire.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is dedicated to the public domain under the [CC0 1.0 Universal (CC0 1.0) Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/). You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.

For more information about CC0, see the [CC0 FAQ](https://wiki.creativecommons.org/wiki/CC0_FAQ).

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the excellent Telegram Bot API wrapper
- The original [pollbot.py example](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/pollbot.py) which served as the foundation for this project
