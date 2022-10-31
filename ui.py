#!/usr/bin/env python

from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import glob
import os
from pathlib import Path
from data_gathering import generate_score
import datetime
import json
import flask

scores = (0.5, 0.2, 0.2, 0.1)

path = '/root/iphone-tracker/processed-data/'
all_files = list(Path(path).glob('*.csv'))

dfs = []

for filename in all_files:
    df = pd.read_csv(filename, header=0, index_col=None, parse_dates=['date'])
    dfs.append(df)

df = pd.concat(dfs, axis=0, ignore_index=True)

df_last_week = df[df['date'] > (datetime.datetime.today() - datetime.timedelta(days=7))]
df_last_week.drop(columns=['date'], inplace=True)
df_last_week.drop_duplicates(inplace=True)
generate_score(df_last_week, *scores)

df_nlargest = df_last_week.nlargest(5, 'score')[['type', 'price', 'bat_health', 'sentiment', 'gb', 'link']]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets, update_title=None)
server = app.server

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='avg_price'),
        dcc.Graph(id='avg_price_relative_to_actual'),
        html.Button('Refresh', id='refresh', n_clicks=0, style = dict(display='none')),
    ], style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='best_phone',
                  hoverData={'points': [{'customdata': ''}]}),
        dcc.Markdown('#### Breakdown of top 5 scoring phones'),
        dash_table.DataTable(df_nlargest.to_dict('records'),
                             [{"name": i, "id": i, 'presentation': 'markdown'} if i == 'link' else {"name": i, "id": i} for i in df_nlargest.columns],
                             id = 'best_scores_table'
                             ),
        html.Br(),
        html.Div([
            html.Div([
                dcc.Markdown('Price Weight'),
                dcc.Input(id='price_weight', value=scores[0], type='number', min=0, max=1.0, step=0.1),
                dcc.Markdown('Battery Health Weight'),
                dcc.Input(id='bat_weight', value=scores[1], type='number', min=0, max=1.0, step=0.1),
            ], style = {'width': '49%', 'float': 'left'}),
            html.Div([
                dcc.Markdown('Storage Weight'),
                dcc.Input(id='gb_weight', value=scores[2], type='number', min=0, max=1.0, step=0.1),
                dcc.Markdown('Sentiment Weight'),
                dcc.Input(id='sentiment_weight', value=scores[3], type='number', min=0, max=1.0, step=0.1),
                ],  style = {'width': '49%', 'float': 'right'})
            ]),
    ], style={'float': 'right', 'width': '49%'}),
])

@app.callback(
    Output('best_scores_table', 'data'),
    Input('price_weight', 'value'),
    Input('bat_weight', 'value'),
    Input('gb_weight', 'value'),
    Input('sentiment_weight', 'value')
)
def update_data_table(price_weight, bat_weight, gb_weight, sentiment_weight):
    generate_score(df_last_week, price_weight, bat_weight, gb_weight, sentiment_weight)
    return df_last_week.nlargest(5, 'score')[['type', 'price', 'bat_health', 'sentiment', 'gb', 'link']].to_dict('records')

@app.callback(
    Output('avg_price', 'figure'),
    Input('refresh', 'n_clicks')
)
def update_avg_price(n_clicks):
    dff = df.groupby(['date', 'type'])['price'].mean().reset_index().rename(columns = {'price': 'average_price'})
    fig = px.scatter(dff, x='date', y='average_price', color='type', title = 'Average Price vs Dates Per Iphone')
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
    fig = px.scatter(dff, x='date', y='percent_diff', color='type', title= 'Percent Difference of Actual Price vs Date Per Iphone')
    fig.update_traces(mode='lines+markers')
    return fig

@app.callback(
    Output('best_phone', 'figure'),
    Input('refresh', 'n_clicks'),
    Input('best_scores_table', 'data')
)
def update_best_phone(n_clicks, data):
    dff = df_last_week.nlargest(20, 'score')
    return px.bar(dff, x=range(len(dff)), y='score', hover_data=['type', 'price', 'bat_health', 'sentiment', 'gb'], title='Top 20 scoring phones of last week')

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
