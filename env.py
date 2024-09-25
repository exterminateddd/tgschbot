WEEKDAYS = 'Z понедельник вторник среда четверг пятница суббота воскресенье'.split(' ')
week_type = lambda isocal: "верхняя" if isocal.week%2==0 else "нижняя"
is_user_admin = lambda user: user.name.lstrip('@') in map(lambda name: name.strip().strip('\n').strip().lstrip('@'), open('admins.txt', 'r', encoding='utf-8').readlines())
