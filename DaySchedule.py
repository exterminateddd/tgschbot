from env import WEEKDAYS


class DaySchedule:
    def __init__(self, week_data, isocal) -> None:
        self.week_data = week_data
        self.isocal = isocal
        self.data = [i for i in filter(lambda d: d["weekday"].lower()==WEEKDAYS[isocal.weekday], week_data[isocal.week%2])]

    @property
    def is_empty(self): return len(self.data)==0

    def text(self) -> str:
        if self.is_empty: return f"{WEEKDAYS[self.isocal.weekday].title()}: пар нет"
        data = self.data[0]
        classes = data['classes']
        weekday = data['weekday']

        text = f"{weekday}\n\n"
        
        for c in classes:
            class_text = f"{c['time']} {c['class_type']}\n<b>{c['class']}</b>\n<i>{c['teacher']}</i>\nАудитория: <b><i>{c['room']}</i></b>"
            text += f'{class_text}\n\n'
        if not classes: text += f'пар нет'
        
        return text.strip('\n')
