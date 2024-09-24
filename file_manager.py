import datetime, json


def get_group_list() -> list:
    return list(json.loads(open('./data/group_codes.json', 'r+').read()).keys())


def work_with_json(user):
    contents = open('./data/users.json', 'r', encoding='UTF-8').read()
    users = {} if not contents else json.loads(contents)

    with open('./data/users.json', 'w+', encoding='UTF-8') as file:
        if str(user.id) not in users:
            users[str(user.id)] = {'name': user.name, 'joined_at': datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}
        file.write(json.dumps(users, indent=4))
