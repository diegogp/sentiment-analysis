import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
import sqlite3
import pandas as pd

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H2('Análise de sentimentos em tweets #flamengo',
                style={'text-align': 'center'}),
        dcc.Graph(id='live-graph'),
        dcc.Interval(
            id='graph-update',
            interval=1000 * 60 * 1,  # 1 minute
            n_intervals=0
        )
    ]
)


@app.callback(Output('live-graph', 'figure'),
              [Input('graph-update', 'n_intervals')])
def update_graph(n):
    #df = pd.read_sql("SELECT * FROM tweets WHERE text LIKE ? ORDER BY unix DESC LIMIT 1000", conn ,params=('%' + sentiment_term + '%',))

    try:
        conn = sqlite3.connect('tweets.db')
        #c = conn.cursor()
        sql = "select (datetime(datetime(created_at), '-3 hours')) as created_at, id_str, sentiment FROM tweets"
        # WHERE julianday(datetime('now')) - julianday(datetime(created_at)) < 1 ORDER BY created_at"
        df = pd.read_sql_query(
            sql, con=conn, index_col=None, parse_dates=['created_at'])
        result = df.groupby([pd.Grouper(key='created_at', freq='5min'), 'sentiment']).count() \
            .unstack(fill_value=0).stack().reset_index()

        fig = px.line(result,
                      x="created_at", y="id_str", color='sentiment')
        fig.update_layout(  # title='Análise de sentimentos em tweets #flamengo',
            xaxis_title='Série Temporal',
            yaxis_title='Número de menções #flamengo')
        return fig

    except Exception as e:
        with open('errors.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')


if __name__ == '__main__':
    app.run_server(debug=True)
