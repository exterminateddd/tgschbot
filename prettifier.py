def prettify(day_schedule: dict) -> str:
    classes = day_schedule['classes']
    weekday = day_schedule['weekday']

    text = f"{weekday}\n\n"
    
    for c in classes:
        class_text = f"{c['time']} {c['class_type']}\n<b>{c['class']}</b>\n<i>{c['teacher']}</i>\nАудитория: <b><i>{c['room']}</i></b>"
        text += f'{class_text}\n\n'
    if not classes: text += f'пар нет'
    
    return text.strip('\n')
