import logging, json, datetime, sys

from prettifier import prettify
from parser import update as update_
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from file_manager import work_with_json, get_group_list

WEEKDAYS = 'Z понедельник вторник среда четверг пятница суббота воскресенье'.split(' ')

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

week_type = lambda isocal: "верхняя" if isocal.week%2==0 else "нижняя"


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

    today = datetime.datetime.today()
    isocal = today.isocalendar()
    tomorrow = (datetime.datetime.today() + datetime.timedelta(days=1))
    isocal_tomorrow = tomorrow.isocalendar()

    logger.info(f'user pressed button with action {query.data}, name: {update.effective_user.name}, id: {update.effective_user.id}')

    group = query.data.split('_')[-1]
    
    if not query.data.startswith('group_choice'):
        try:
            data = json.loads(open(f'./data/{group}.json').read())['data']
        except FileNotFoundError as err:
            await update.effective_user.send_message('please contact @susumantgnet, no data found for selected group')
            logger.error(f"no data for group {group}, requested by name: {update.effective_user.name}, " + \
                    "id: {update.effective_user.id}")
            return

    if query.data.startswith('schedule_for_'):
        await update.effective_user.send_message(f'щас {week_type(isocal)} неделя, {WEEKDAYS[isocal.weekday]}')
        data_for_today = [i for i in filter(lambda d: d["weekday"].lower()==WEEKDAYS[isocal.weekday], data[isocal.week%2])]

        keyboard = [
            [InlineKeyboardButton('а завтра что будет', callback_data=f"tomorrow_schedule_for_{group}")],
            [InlineKeyboardButton('расписание на неделю вперед', callback_data=f"week_schedule_for_{group}")]
        ]
        kb_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_user.send_message(f'{prettify(data_for_today[0]) if data_for_today else "сегодня отдыхаем"}', parse_mode='HTML', reply_markup=kb_markup)
        await query.edit_message_text(text=f"вы выбрали группу {query.data.split('_', 2)[2]}")
    if query.data.startswith('tomorrow_schedule_for_'):
        await update.effective_user.send_message(f'завтра {week_type(isocal_tomorrow)} неделя, {WEEKDAYS[isocal_tomorrow.weekday]}')
        data_for_tomorrow = [i for i in filter(lambda d: d["weekday"].lower()==WEEKDAYS[isocal_tomorrow.weekday], data[isocal_tomorrow.week%2])]
        if not data_for_tomorrow:
            await update.effective_user.send_message('завтра отдыхаем!!!')
        else:
            await update.effective_user.send_message(f'{prettify(data_for_tomorrow[0])}', parse_mode='HTML')
        await query.edit_message_reply_markup(reply_markup = '')
    if query.data.startswith('week_schedule_for_'):
        text = ""
        timestamp = today
        for j in range(7):
            isocal_jth = timestamp.isocalendar()
            data_for_jth_day = [i for i in filter(lambda d: d["weekday"].lower()==WEEKDAYS[isocal_jth.weekday], data[isocal_jth.week%2])]
            text += '\n'+prettify(data_for_jth_day[0] if data_for_jth_day else {'weekday': WEEKDAYS[isocal_jth.weekday].title(), 'classes': []})+'\n\n'
            timestamp += datetime.timedelta(days=1)
        await query.edit_message_reply_markup(reply_markup = '')
        await update.effective_user.send_message(text, parse_mode = 'HTML')

    if query.data.startswith('group_choice_for_year_'):
        chosen_year = query.data.split('_')[-1]
        keyboard = [[InlineKeyboardButton(f"{group}", callback_data=f"schedule_for_{group}")] for group in get_group_list() if group.endswith(chosen_year)]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_user.send_message(
            "Please select your group",
            reply_markup=reply_markup, parse_mode='HTML'
        )


async def update_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('yessssss!!! updating in progress')
    try:
        update_()
    except Exception as e:
        await update.effective_user.send_message(f'critical error during update, manual fix might be needed')
        logger.error('critical error while updating data')
    await update.effective_user.send_message('done.')


async def getusers_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('getting user list')
    data = json.loads(open('./data/users.json', encoding='UTF-8').read())
    await update.effective_user.send_message(f"total user number: {len(data)}")
    await update.effective_user.send_message('\n\n'.join(map(lambda item: (lambda k, v: f'name: {v["name"]}\nid: {k}\njoined at {v["joined_at"]}')(*item), data.items())))


def main() -> None:
    application = Application.builder().token(open('token.txt', 'r').read()).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ZZZVVVZAROSSIYU", update_command))
    application.add_handler(CommandHandler("ZZZVVVZAROSSIYU1", getusers_command))

    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
