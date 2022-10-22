#!/usr/bin/env python

from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import glob
import os
from pathlib import Path
from data_gathering import generate_score
import datetime

path = '/Users/sacha/Repos/iphone-tracker/data/'
all_files = list(Path(path).glob('*.csv'))

dfs = []

for filename in all_files:
    df = pd.read_csv(filename, header=0, index_col=None, parse_dates=['date'])
    dfs.append(df)

df = pd.concat(dfs, axis=0, ignore_index=True)

df_last_week = df[df['date'] > (datetime.datetime.today() - datetime.timedelta(days=7))]
df_last_week.drop(columns=['date'], inplace=True)
df_last_week.drop_duplicates(inplace=True)
generate_score(df_last_week)

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='avg_price'),
        dcc.Graph(id='avg_price_relative_to_actual'),
        html.Button('Refresh', id='refresh', n_clicks=0),
    ], style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='best_phone'),
        dcc.Markdown(id='best_phone_description')
    ], style={'float': 'right', 'width': '49%'}),
])

@app.callback(
    Output('avg_price', 'figure'),
    Input('refresh', 'n_clicks')
)
def update_avg_price(n_clicks):
    dff = df.groupby(['date', 'type'])['price'].mean().reset_index().rename(columns = {'price': 'average_price'})
    fig = px.scatter(dff, x='date', y='average_price', color='type')
    fig.update_traces(mode='lines+markers')
    return fig


@app.callback(
    Output('avg_price_relative_to_actual', 'figure'),
    Input('refresh', 'n_clicks')
)
def update_avg_price_relative_to_actual(n_clicks):
    prices = {'iphone-11': 550.0, 'iphone-12': 849.0, 'iphone-12-mini': 625.0}
    dff = df.groupby(['date', 'type'])['price'].mean().reset_index().rename(columns = {'price': 'average_price'})
    for k,v in prices.items():
        dff.loc[dff['type']==k, 'average_price'] = (abs(dff['average_price'] - v))/v
    dff.rename(columns={'average_price': 'percent_diff'}, inplace=True)
    fig = px.scatter(dff, x='date', y='percent_diff', color='type')
    fig.update_traces(mode='lines+markers')
    return fig

@app.callback(
    Output('best_phone', 'figure'),
    Input('refresh', 'n_clicks')
)
def update_best_phone(n_clicks):
    dff = df_last_week.nlargest(5, 'score')
    return px.bar(dff, x=range(5), y='score', hover_data=['type', 'price', 'bat_health'])

@app.callback(
    Output('best_phone_description', 'children'),
    Input('best_phone', 'hoverData')
)
def update_text_box(hoverData):
    return 'This is the {}'.format(hoverData['points'][0]['price'])

if __name__ == '__main__':
    app.run_server(debug=True)
