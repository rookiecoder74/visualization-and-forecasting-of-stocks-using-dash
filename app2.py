import dash
from dash import Dash, html, dcc
from datetime import datetime as dt
from datetime import timedelta
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from dash import dash_table

from model import prediction
from sklearn.svm import SVR

# def fetch_csv_data():
#     end_date = dt.now().date()
#     start_date = end_date - timedelta(days=5)

#     dat = pd.date_range(start=start_date, end=end_date, freq='B')

#     header_written = False
#     for d in dat:
#         dmy = d.strftime('%d%m%Y')
#         url1 = 'https://archives.nseindia.com/content/nsccl/fao_participant_oi_' + dmy + '.csv'
#         data1 = pd.read_csv(url1, skiprows=1)
#         data1.insert(0, 'Date', d)
#         data1.columns = [c.strip() for c in data1.columns.values.tolist()]
#         data1 = data1.iloc[:, :6]

#         if header_written:
#             data1.to_csv('open.csv', index=False, mode='a', header=False)
#         else:
#             data1.to_csv('open.csv', index=False, mode='a', header=True)
#             header_written = True


def get_stock_price_fig(df):

    fig = px.line(df,
                  x="Date",
                  y=["Close", "Open"],
                  title="Closing and Opening Price vs Date For Requested Stock/Index")

    return fig


def get_more(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df,
                     x="Date",
                     y="EMA_20",
                     title="Exponential Moving Average vs Date For Requested Stock/Index")
    fig.update_traces(mode='lines+markers')
    return fig


app = dash.Dash(__name__,
    external_stylesheets=[
        "style.css"
    ])
server = app.server
# html layout of site
app.layout = html.Div(
    [
        html.Div(
            [
                # Navigation
                html.P("THE STOCK DASH APP", className="start"),
                html.Div([
                    html.P("Input a stock code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers", type="text"),
                        html.Button("Submit", id='submit'),
                    ],
                             className="form")
                ],
                         className="input-place"),
                html.Div([
                    dcc.DatePickerRange(id='my-date-picker-range',min_date_allowed=dt(1995, 8, 5),max_date_allowed=dt.now(),initial_visible_month=dt.now(),end_date=dt.now().date()),
                ],
                         className="date"),
                html.Div([
                    html.Button(
                        "Stock Price", className="stock-btn", id="stock"),
                    html.Button("Indicators",className="indicators-btn",id="indicators"),
                    
                    html.Button(
                        "Forecast", className="forecast-btn", id="forecast"),

                    dcc.Input(id="n_days",type="text",placeholder="Input number of days")
                ],
                         className="buttons"),
            ],
            className="nav"),

        # content
        html.Div(
            [
                html.Div(
                    [  # header
                        #html.Img(id="logo"),
                        html.P(id="ticker")
                    ],
                    className="header"),
                html.Div(id="description", className="decription_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content"),
                html.Div([], id="csv-table"),
                html.Div([], id="nifty-content"),
            ],
            className="content"),
    ],
    className="container")


# callback for company info
@app.callback([
    Output("description", "children"),
    #Output("logo", "src"),
    Output("ticker", "children"),
    Output("stock", "n_clicks"),
    Output("indicators", "n_clicks"),
    Output("forecast", "n_clicks")
], [Input("submit", "n_clicks")], [State("dropdown_tickers", "value")])
def update_data(n, val):  # input parameter(s)
    if n == None:
        return "Data Visualization in stock market helps traders when making decisions quickly and enables them to easily synthesize large amount of complex information. *Enter a legitimate stock code to get the details.* ", "STOCKS FORECASTER AND VISUALIZER", None, None, None
    else:
        if val == None:
            raise PreventUpdate
        else:
            ticker = yf.Ticker(val)
            inf = ticker.info
            df = pd.DataFrame().from_dict(inf, orient="index").T
            df[['shortName', 'longBusinessSummary']]
            return df['longBusinessSummary'].values[0], df['shortName'].values[0], None, None,None #,#None
        
# callback for stocks graphs
@app.callback([
    Output("graphs-content", "children"),
], [
    Input("stock", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def stock_price(n, start_date, end_date, val):
    if n == None:
        return [""]
        #raise PreventUpdate
    if val == None:
        raise PreventUpdate
    else:
        if start_date != None:
            df = yf.download(val, str(start_date), str(end_date))
        else:
            df = yf.download(val)

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]


# callback for indicators
@app.callback([Output("main-content", "children")], [
    Input("indicators", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def indicators(n, start_date, end_date, val):
    if n == None:
        return [""]
    if val == None:
        return [""]

    if start_date == None:
        df_more = yf.download(val)
    else:
        df_more = yf.download(val, str(start_date), str(end_date))

    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig)]


# callback for forecast
# callback for forecast and CSV table
@app.callback(
    [Output("nifty-content","children"),Output("forecast-content", "children"), Output("csv-table", "children")],
    [Input("forecast", "n_clicks")],
    [State("n_days", "value"), State("dropdown_tickers", "value")],
    prevent_initial_call=True
)
def forecast_and_csv_table(n, n_days, val):
    if n is None:
        return [""],[""], None

    if val is None:
        raise PreventUpdate

    end_date = dt.now().date()
    start_date = end_date - timedelta(days=30)
    nifty_data = yf.download("^NSEI", start=start_date, end=end_date)
    fig2={
            "data": [
                go.Scatter(
                    x=nifty_data.index,
                    y=nifty_data["Close"],
                    mode="lines",
                    name="Nifty50",
                ),
            ],
            "layout": go.Layout(
                title="Nifty50 Index Price For Past 30 Days",
                xaxis={"title": "Date"},
                yaxis={"title": "Price"},
            ),
        }
    # Generate the forecasted graph
    fig = prediction(val, int(n_days) + 1)
    #fetch_csv_data()
    csv_data = pd.read_csv('open.csv')
    # Check if the CSV data is available
    if csv_data is None:
        return dcc.Graph(figure=fig2),dcc.Graph(figure=fig), None

    # Generate the table using dash_table.DataTable
    csv_table = dash_table.DataTable(
        data=csv_data.to_dict("records"),
        columns=[{"name": col, "id": col} for col in csv_data.columns],
        style_table={"overflowX": "scroll", "color": "black"},
        style_cell={"textAlign": "left"},
    )

    return dcc.Graph(figure=fig2),dcc.Graph(figure=fig),csv_table

if __name__ == '__main__':
    app.run_server(port="8050",debug=True)
