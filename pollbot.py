#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz  # You'll need to install this: pip install pytz

# Load environment variables
load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Set up Google Sheets API
creds = Credentials.from_service_account_file('gsheets-key.json')
service = build('sheets', 'v4', credentials=creds)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

from telegram import (
    KeyboardButton,
    KeyboardButtonPollType,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Modify the QUESTIONNAIRE to include question identifiers
QUESTIONNAIRE = [
    {
        "id": "favorite_color",
        "type": "multiple_choice",
        "question": "What's your favorite color?",
        "options": ["Red", "Blue", "Green", "Yellow"]
    },
    {
        "id": "favorite_car",
        "type": "multiple_choice",
        "question": "What's your favorite car?",
        "options": ["Renault", "Nissan", "Toyota", "Skoda"]
    },
    {
        "id": "ideal_vacation",
        "type": "open_ended",
        "question": "Describe your ideal vacation:"
    },
]

# Modify the save_answer function to use the correct type hint
def save_answer(context: ContextTypes.DEFAULT_TYPE, user_id, question_id, answer):
    if user_id not in context.bot_data:
        context.bot_data[user_id] = {}
    context.bot_data[user_id][question_id] = answer

# Add a new function to save the complete questionnaire to Google Sheets
def save_questionnaire_to_sheets(context: ContextTypes.DEFAULT_TYPE, user_id):
    sheet = service.spreadsheets()
    
    # Get the current timestamp
    timestamp = datetime.now(pytz.timezone('Asia/Baku')).strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare the row data
    row_data = [timestamp, user_id]
    for question in QUESTIONNAIRE:
        answer = context.bot_data[user_id].get(question['id'], '')
        if question['type'] == 'multiple_choice':
            answer = question['options'][int(answer)] if answer != '' else ''
        row_data.append(answer)
    
    # Check if the sheet is empty (no headers)
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A1:Z1').execute()
    values = result.get('values', [])
    
    if not values:
        # If the sheet is empty, add headers first
        headers = ['Timestamp', 'User ID'] + [q['id'] for q in QUESTIONNAIRE]
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A1',
            valueInputOption='USER_ENTERED',
            body={'values': [headers]}
        ).execute()
    
    # Append the row to the sheet
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:Z',  # Adjust as needed
        valueInputOption='USER_ENTERED',
        body={'values': [row_data]}
    ).execute()
    
    # Clear the user's data from bot_data
    del context.bot_data[user_id]



TOTAL_VOTER_COUNT = 1000


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform user about what this bot can do"""
    await update.message.reply_text(
        "Please select /poll to get a Poll, /quiz to get a Quiz or /preview"
        " to generate a preview for your poll"
    )


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a predefined poll"""
    questions = ["Good", "Really good", "Fantastic", "Great"]
    message = await context.bot.send_poll(
        update.effective_chat.id,
        "How are you?",
        questions,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "questions": questions,
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
            "answers": 0,
        }
    }
    context.bot_data.update(payload)


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
    await context.bot.send_message(
        answered_poll["chat_id"],
        f"{update.effective_user.mention_html()} feels {answer_string}!",
        parse_mode=ParseMode.HTML,
    )
    answered_poll["answers"] += 1
    # Close poll after three participants voted
    if answered_poll["answers"] == TOTAL_VOTER_COUNT:
        await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a predefined poll"""
    questions = ["1", "2", "4", "20"]
    message = await update.effective_message.reply_poll(
        "How many eggs do you need for a cake?", questions, type=Poll.QUIZ, correct_option_id=2
    )
    # Save some info about the poll the bot_data for later use in receive_quiz_answer
    payload = {
        message.poll.id: {"chat_id": update.effective_chat.id, "message_id": message.message_id}
    }
    context.bot_data.update(payload)


async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close quiz after three participants took it"""
    # the bot can receive closed poll updates we don't care about
    if update.poll.is_closed:
        return
    if update.poll.total_voter_count == TOTAL_VOTER_COUNT:
        try:
            quiz_data = context.bot_data[update.poll.id]
        # this means this poll answer update is from an old poll, we can't stop it then
        except KeyError:
            return
        await context.bot.stop_poll(quiz_data["chat_id"], quiz_data["message_id"])


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user to create a poll and display a preview of it"""
    # using this without a type lets the user chooses what he wants (quiz or poll)
    button = [[KeyboardButton("Press me!", request_poll=KeyboardButtonPollType())]]
    message = "Press the button to let the bot generate a preview for your poll"
    # using one_time_keyboard to hide the keyboard
    await update.effective_message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(button, one_time_keyboard=True)
    )


async def receive_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    # Only need to set the question and options, since all other parameters don't matter for
    # a closed poll
    await update.effective_message.reply_poll(
        question=actual_poll.question,
        options=[o.text for o in actual_poll.options],
        # with is_closed true, the poll/quiz is immediately closed
        is_closed=True,
        reply_markup=ReplyKeyboardRemove(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a help message"""
    await update.message.reply_text("Use /quiz, /poll or /preview to test this bot.")


async def start_questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    context.bot_data[user_id] = {}
    context.user_data['current_question'] = 0
    context.user_data['chat_id'] = update.effective_chat.id
    await send_next_question(update, context)


async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_question = context.user_data['current_question']
    chat_id = context.user_data.get('chat_id')
    user_id = update.effective_user.id if update.effective_user else context.user_data.get('user_id')
    
    if current_question < len(QUESTIONNAIRE):
        question = QUESTIONNAIRE[current_question]
        if question['type'] == 'multiple_choice':
            await context.bot.send_poll(
                chat_id,
                question['question'],
                question['options'],
                is_anonymous=False,
                allows_multiple_answers=False,
            )
        elif question['type'] == 'open_ended':
            await context.bot.send_message(chat_id, question['question'])
        context.user_data['current_question'] += 1
    else:
        await context.bot.send_message(chat_id, "Thank you for completing the questionnaire!")
        save_questionnaire_to_sheets(context, user_id)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    question_id = QUESTIONNAIRE[context.user_data['current_question'] - 1]['id']
    save_answer(context, user_id, question_id, update.message.text)
    await send_next_question(update, context)


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answer = update.poll_answer
    user_id = update.effective_user.id
    question_id = QUESTIONNAIRE[context.user_data['current_question'] - 1]['id']
    save_answer(context, user_id, question_id, str(answer.option_ids[0]))
    context.user_data['user_id'] = user_id  # Store user_id for later use
    await send_next_question(update, context)


def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_questionnaire))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(MessageHandler(filters.POLL, receive_poll))
    application.add_handler(PollHandler(receive_quiz_answer))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
