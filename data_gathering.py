#!/usr/bin/env python

import requests as req
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import regex as re
import random
import time

def clean_text(text, key=None):
    '''
    Cleans the text by stripping whitespace, removing newlines, and symbols
    @param: <str> text
    @param: <str> key - specifies the type of information embedded in the text
    @returns <str> cleaned text
    '''
    if key == 'distance':
        text = text.replace("km", "")
        if str.__contains__(text, 'Near you'):
            return None
    return text.replace("\n", "").replace("$", "").replace("<", "").strip()

def gather_data(keyword):
    '''
    Gathers the iphone mini 12 data from kijiji, cleans it and puts it into a Pandas DataFrame
    @return <pandas.DataFrame> columns - [title, price, distance, description]
    '''
    keys = ['price', 'title', 'distance', 'description']
    phones = []
    is_next = True
    page_number = 1

    while is_next:
        url = 'https://www.kijiji.ca/b-cell-phone/ottawa/{}/page-{}/k0c760l1700185?rb=true&ll=45.421530%2C-75.697193&address=Ottawa%2C+ON&radius=50.0'.format(keyword, page_number)
        response = req.get(url)
        soup = BeautifulSoup(response.content, features="html.parser")
        datas = soup.find_all("div", class_="info-container")
        for data in datas:
            phone = {}
            for key in keys:
                phone[key] = clean_text(data.find("div", class_=key).text, key)
                if key == 'title':
                    phone['link'] = data.find("div", class_=key).href
            phones.append(phone)


        if soup.find("div", class_="pagination").find("a", title="Next") is not None:
            is_next = True
            page_number += 1
        else:
            is_next = False

    print('Gathered {} rows on {}'.format(len(phones), keyword))
    df = pd.DataFrame(phones)

    # Perform cleaning and calculations

    # Spam cleaning
    df = df[(~df.description.str.contains('CELLULAR') & ~df.description.str.contains('FLEX') & ~df.description.str.contains('New in stock')
             & ~df.description.str.contains('Buy') & ~df.description.str.contains('buying'))]

    # Remove the non-price rows
    df = df[pd.to_numeric(df['price'], errors='coerce').notnull()]
    df = df[df['price']>200]

    # Add date
    df['date'] =  pd.Timestamp(datetime.datetime.today().strftime('%Y-%m-%d'))

    # Add Battery Health calculation and filling
    df['bat_health'] = df.apply(lambda x: battery_health(x.description), axis=1)
    df['bat_health'].fillna(df['bat_health'].min(), inplace=True)

    df['type'] = keyword

    return df

def battery_health(text):
    match = re.findall(r'(\d+?%)',text)
    if len(match) != 0:
        bat_health = int(match[0].strip().replace("%", ""))
        return bat_health / 100.0
    else:
        if str.__contains__(text.lower(), 'sealed'):
            return 1.0
        return None

def sentiment_analysis(text):
    bad_words = set(['cracked', 'crack', 'broken'])
    words = set(text.split(" "))
    num_bad_matches = len(bad_words.intersection(words))
    return num_bad_matches

def num_gb(text):
    pass

def generate_score(df):

    def score(row):
        return 0.7 * (1/float(row.price))/ max_price_per_type[row.type] + 0.3 * row.bat_health

    df_min_price = df.groupby('type')['price'].min().reset_index()
    df_min_price['price'] = 1/df_min_price['price']
    max_price_per_type = {r['type']:r['price'] for r in df_min_price.to_dict(orient='records')}

    df['score'] = df.apply(lambda x: score(x), axis=1)

if __name__ == '__main__':
    for idx, search_term in enumerate(['iphone-11', 'iphone-12', 'iphone-12-mini']):
        df = gather_data(keyword=search_term)
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        df.to_csv('data/data_{}_{}.csv'.format(search_term, today), index=False)
        if idx < 2:
            time.sleep(random.randrange(30, 60))
