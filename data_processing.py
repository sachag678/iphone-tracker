#!/usr/bin/env python

from bs4 import BeautifulSoup
import pandas as pd
import datetime
import regex as re
from pathlib import Path
from textblob import TextBlob
import sys


def process_data(keyword, today):
    """
    Process the data from the data-lake.
    @param <str> keyword
    @param <str> today's date in the format yy-mm-dd
    """
    path = "data-lake/" + keyword + "/" + today + "/"
    all_files = list(Path(path).glob("*.html"))

    keys = ["price", "title", "distance", "description"]
    phones = []

    for file in all_files:
        with open(file, "r") as f:
            content = f.read()
            soup = BeautifulSoup(content, features="html.parser")
            datas = soup.find_all("div", class_="info-container")
            for data in datas:
                phone = {}
                for key in keys:
                    phone[key] = clean_text(data.find("div", class_=key).text, key)
                    if key == "title":
                        phone["link"] = '[Link](https://www.kijiji.ca' + data.find("div", class_=key).find(
                            "a", class_=key
                        )["href"] + ")"
                phones.append(phone)
    print("Gathered {} rows on {}".format(len(phones), keyword))
    df = pd.DataFrame(phones)

    # Spam cleaning
    df = df[
        (
            ~df.description.str.contains("CELLULAR")
            & ~df.description.str.contains("FLEX")
            & ~df.description.str.contains("New in stock")
            & ~df.description.str.contains("Buy")
            & ~df.description.str.contains("buying")
            & ~df.title.str.lower().str.contains("repair")
        )
    ]

    # Validation of title to ensure it is the correct phone
    # Check if each keyword is present in the title.
    keywords = r'^'
    for key in keyword.split("-"):
        keywords += '(?=.*{})'.format(key)
    df = df[df.title.str.lower().str.contains(keywords)]

    # Remove the non-price rows and convert to numeric
    df = df[pd.to_numeric(df["price"], errors="coerce").notnull()]
    df["price"] = df["price"].apply(pd.to_numeric)
    df = df[df["price"] > 200]

    # Add date
    df["date"] = pd.Timestamp(today)

    # Add Battery Health calculation and filling
    df["bat_health"] = df.apply(lambda x: battery_health(x.description), axis=1)
    df["bat_health"].fillna(df["bat_health"].min(), inplace=True)

    # Add GB
    df["gb"] = df.apply(lambda x: num_gb(x.description + ' ' + x.title), axis=1)

    # Add sentiment
    df["sentiment"] = df.apply(lambda x: sentiment_analysis(x.description), axis=1)

    # Add keyword
    df["type"] = keyword

    # Save to file
    df.to_csv("processed-data/data_{}_{}.csv".format(keyword, today), index=False)


def clean_text(text, key=None):
    """
    Cleans the text by stripping whitespace, removing newlines, and symbols
    @param: <str> text
    @param: <str> key - specifies the type of information embedded in the text
    @returns <str> cleaned text
    """
    if key == "distance":
        text = text.replace("km", "")
        if str.__contains__(text, "Near you"):
            return None
    return text.replace("\n", "").replace("$", "").replace("<", "").strip()


def battery_health(text):
    match = re.findall(r"(\d+?%)", text)
    if len(match) != 0:
        bat_health = int(match[0].strip().replace("%", ""))
        return bat_health / 100.0
    else:
        if str.__contains__(text.lower(), "sealed"):
            return 1.0
        return None


def sentiment_analysis(text):
    bad_words = set(["cracked", "crack", "broken", "cracks", "scratches", "scratching"])
    words = set(text.split(" "))
    num_bad_matches = len(bad_words.intersection(words))
    if num_bad_matches > 0:
        return -1.0
    blob = TextBlob(text)
    return round(blob.sentiment.polarity * (1 - blob.sentiment.subjectivity), 2)

def num_gb(text):
    match = re.findall(r"\d+?GB", text.upper())
    other_match = re.findall(r"\d+?\sGB", text.upper())
    if len(match) != 0:
        return int(match[0].strip().replace("GB", ""))
    elif len(other_match) != 0:
        return int(other_match[0].replace("GB", "").strip())
    else:
        return 32


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        num_prev_days = int(args[0])
    else:
        num_prev_days = 0
    keywords = ["iphone-11", "iphone-12", "iphone-12-mini"]
    for prev in range(num_prev_days + 1):
        today = (datetime.datetime.today() - datetime.timedelta(days=prev)).strftime("%Y-%m-%d")
        for keyword in keywords:
                process_data(keyword, today)
