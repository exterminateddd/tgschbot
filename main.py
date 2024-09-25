import logging, json, datetime, sys

from DaySchedule import DaySchedule
from parser import update as update_
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from file_manager import work_with_json, get_group_list
from env import WEEKDAYS, week_type, is_user_admin

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig()

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(filename='general.log', encoding='utf-8')

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger(__name__).setLevel(logging.INFO)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    logger.info(f'user sent /start, name: {user.name}, id: {user.id}')
    try:
        work_with_json(user)
        logger.info('successfully updated users.json')
    except Exception as e:
        logger.info(e)
        logger.info('failed to update users.json, terminated with error above')

    keyboard = sorted([
        [InlineKeyboardButton(f"{year}", callback_data=f"group_choice_for_year_{year}")] for year in set([g[-2:] for g in list(get_group_list())])
    ], key=lambda ikbl: ikbl[0].text) # sort InlineKeyboardButton sequences by their first elements' "text" property since all buttons are single

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        f"Hi {user.mention_html()}! " + 
        "please choose your enrollment year",
        reply_markup=reply_markup
    )


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    u = update.effective_user

    today = datetime.datetime.today()
    isocal = today.isocalendar()
    tomorrow = (datetime.datetime.today() + datetime.timedelta(days=1))
    isocal_tomorrow = tomorrow.isocalendar()

    logger.info(f'user pressed button with action {query.data}, name: {u.name}, id: {u.id}')

    group = query.data.split('_')[-1]
    
    if not query.data.startswith('group_choice'):
        try:
            data = json.loads(open(f'./data/{group}.json').read())['data']
        except FileNotFoundError as err:
            await u.send_message('please contact @susumantgnet, no data found for selected group')
            logger.error(f"no data for group {group}, requested by name: {u.name}, " + \
                    "id: {u.id}")
            return

    if query.data.startswith('schedule_for_'):
        await u.send_message(f'щас {week_type(isocal)} неделя, {WEEKDAYS[isocal.weekday]}')
        schedule_for_today = DaySchedule(data, isocal)

        keyboard = [
            [InlineKeyboardButton('а что будет завтра', callback_data=f"tomorrow_schedule_for_{group}")],
            [InlineKeyboardButton('расписание на неделю вперед', callback_data=f"week_schedule_for_{group}")]
        ]
        kb_markup = InlineKeyboardMarkup(keyboard)
        await u.send_message(schedule_for_today.text() if not schedule_for_today.is_empty else "сегодня отдыхаем", \
            parse_mode='HTML', \
            reply_markup=kb_markup)
        await query.edit_message_text(text=f"вы выбрали группу {query.data.split('_', 2)[2]}")
    
    elif query.data.startswith('tomorrow_schedule_for_'):
        msg = ''
        await u.send_message(f'завтра {week_type(isocal_tomorrow)} неделя, {WEEKDAYS[isocal_tomorrow.weekday]}')
        schedule_for_tomorrow = DaySchedule(data, isocal_tomorrow)
        msg = schedule_for_tomorrow.text() if not schedule_for_tomorrow.is_empty else "завтра отдыхаем"
        await u.send_message(msg, parse_mode='HTML')
        await query.edit_message_reply_markup(reply_markup = '')
    elif query.data.startswith('week_schedule_for_'):
        text = ""
        timestamp = today
        for j in range(7):
            isocal_jth = timestamp.isocalendar()
            schedule_for_jth_day = DaySchedule(data, isocal_jth)
            text += '\n'+(schedule_for_jth_day.text())+'\n\n'
            timestamp += datetime.timedelta(days=1)
        await u.send_message(text, parse_mode = 'HTML')
        await query.edit_message_reply_markup(reply_markup = '')

    if query.data.startswith('group_choice_for_year_'):
        chosen_year = query.data.split('_')[-1]
        keyboard = [[InlineKeyboardButton(f"{group}", callback_data=f"schedule_for_{group}")] for group in get_group_list() if group.endswith(chosen_year)]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_user.send_message(
            "Please select your group",
            reply_markup=reply_markup, parse_mode='HTML'
        )


async def update_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_user_admin(u):
        await u.send_message('you are not admin')
        return

    await update.message.reply_text('yessssss!!! updating in progress')
    try:
        update_()
    except Exception as e:
        await u.send_message(f'critical error during update, manual fix might be needed')
        logger.warning(f'non-admin sent admin-only command {update.message.text}, name: {u.name}, id: {u.id}')
        logger.error('critical error while updating data')
    await u.send_message('done.')


async def getusers_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_user_admin(u):
        await u.send_message('you are not admin')
        logger.warning(f'non-admin sent admin-only command {update.message.text}, name: {u.name}, id: {u.id}')
        return
    
    await update.message.reply_text('getting user list')
    data = json.loads(open('./data/users.json', encoding='UTF-8').read())
    await u.send_message(f"total user number: {len(data)}")
    await u.send_message('\n\n'.join(map(lambda item: (lambda k, v: f'name: {v["name"]}\nid: {k}\njoined at {v["joined_at"]}')(*item), data.items())))


def main() -> None:
    application = Application.builder().token(open('token.txt', 'r').read()).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("update_data", update_command))
    application.add_handler(CommandHandler("user_list", getusers_command))

    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
