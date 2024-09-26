from requests import get
from collections import OrderedDict
from datetime import datetime

import bs4
import json
import os

ANNOT = (bs4.NavigableString | bs4.Tag)


def get_group_codes():
    html = open("temp.html", "r", encoding='UTF-8').read()
    soup = bs4.BeautifulSoup(html, 'html.parser')
    options = soup.find('select').find_all('option')
    return {
        o.text: o['value'] for o in options if o['value']
    }

def one_week_to_list(par_div_html):
    D = []
    par_div = par_div_html
    while par_div.find('table') is None: par_div = par_div.find(['div'])
    tbody = par_div.find('table') # gets table correctly, now i have to parse the TR elements

    for tr in tbody.find_all('tr'):
        if tr.find('th') is not None:
            weekday = tr.find('th').text
            D.append({'weekday': weekday, 'classes': []})
        else:
            tds = tr.find_all('td')
            try:
                D[-1]['classes'].append({
                    'time':  tds[0].text,
                    'class': tds[1].text,
                    'class_type': tds[2].text,
                    'teacher': tds[3].text,
                    'room': tds[4].text
                })
            except IndexError: D[-1]['classes'][-1]['teacher'] += f', {tds[0].text}'
    return D


def html_to_list(html: ANNOT, first_week_is_upper=True):
    par_divs = html.find_all('div', class_='tab-pane')
    return [one_week_to_list(par_divs[i]) for i in range(2)][::1 if first_week_is_upper else -1]


def update_group_codes():
    open('./data/group_codes.json', 'w+', encoding='UTF-8').write(json.dumps(get_group_codes(), indent=4))


def update():
    update_group_codes()
    group_codes = get_group_codes()

    for f in os.listdir('./data'):
        if f not in ['group_codes.json', 'users.json']:
            os.remove(f'./data/{f}')

    for group, code in group_codes.items():
        url = f"""https://www.rudn.ru/api/v1/education/schedule?facultet=abdcf766-b523-11e8-82c5-d85de2dacc30&level=16d26142-95f2-11eb-a207-00155d697087&kurs=1&form=%D0%B4&group={code}"""
        #         https://www.rudn.ru/api/v1/education/schedule?facultet=abdcf766-b523-11e8-82c5-d85de2dacc30&level=16d26142-95f2-11eb-a207-00155d697087&kurs=1&form=%D0%B4&group=
        html = get(url).content
        soup = bs4.BeautifulSoup(html, 'html.parser')
        print(url)
        content = soup.find('div').find('div').find('div').find('div', class_='tab-content')
        tries = 0
        while tries < 5:
            try:
                week_list = html_to_list(content, datetime.today().isocalendar().week%2==0)
            except: tries += 1
            else: break
        if tries == 5: raise Exception()

        json_file = open(f'./data/{group}.json', 'w+', encoding='UTF-8')
        json_file.write(json.dumps({'data': week_list}))
