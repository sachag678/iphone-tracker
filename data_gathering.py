#!/usr/bin/env python

import requests as req
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import random
import time
import os
from pathlib import Path
from scipy.special import softmax


def get_data(keyword, today):
    """
    Fetch data from kijiji related to the keyword and store it in the data-lake
    @param <str> keyword
    @param <str> today's date in y-mm-dd format
    """

    # make the directory
    file_path = "data-lake/" + keyword + "/" + today + "/"
    os.makedirs(file_path, exist_ok=True)

    is_next = True
    page_number = 1
    while is_next:
        url = "https://www.kijiji.ca/b-cell-phone/ottawa/{}/page-{}/k0c760l1700185?rb=true&ll=45.421530%2C-75.697193&address=Ottawa%2C+ON&radius=50.0".format(
            keyword, page_number
        )
        response = req.get(url)
        soup = BeautifulSoup(response.content, features="html.parser")

        # write to file
        filename = file_path + "data_{}_{}_page_{}.html".format(
            keyword, today, page_number
        )
        writer = open(filename, "wb")
        writer.write(response.content)
        writer.close()

        # check if another page exists
        if soup.find("div", class_="pagination").find("a", title="Next") is not None:
            is_next = True
            page_number += 1
        else:
            is_next = False


def generate_score(df, price_weight, bat_weight, gb_weight, sentiment_weight):

    weights = softmax([price_weight, bat_weight, gb_weight, sentiment_weight])

    def score(row):
        return (
            weights[0] * (1 / float(row.price)) / max_price_per_type[row.type]
            + weights[1] * row.bat_health
            + weights[2] * (row.gb / 512.0)
            + weights[3] * row.sentiment
        )

    df_min_price = df.groupby("type")["price"].min().reset_index()
    df_min_price["price"] = 1 / df_min_price["price"]
    max_price_per_type = {
        r["type"]: r["price"] for r in df_min_price.to_dict(orient="records")
    }

    df.loc[:, "score"] = df.apply(lambda x: score(x), axis=1)


if __name__ == "__main__":
    keywords = ["iphone-11", "iphone-12", "iphone-12-mini"]
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    for idx, search_term in enumerate(keywords):
        get_data(search_term, today)
        if idx < len(keywords) - 1:
            time.sleep(random.randrange(30, 60))
