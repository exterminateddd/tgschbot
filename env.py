WEEKDAYS = 'Z понедельник вторник среда четверг пятница суббота воскресенье'.split(' ')
week_type = lambda isocal: "верхняя" if isocal.week%2==0 else "нижняя"
is_user_admin = lambda user: user.name.lstrip('@') in open('admins.txt', 'r').readlines()
