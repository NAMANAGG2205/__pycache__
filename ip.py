import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import boto3
import yfinance as yf
import os
import io
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
    print("❌ AWS credentials missing. Check .env or environment variables.")
    sys.exit(1)

TICKER_GROUPS = {
    "US Banks": ['JPM', 'BAC', 'C', 'WFC', 'GS'],
    "US Banks in India": ['JPM', 'WFC', 'C', 'BAC']
}

def get_financial_data(tickers, period="5y"):
    all_data = {}
    for ticker in tickers:
        print(f"Fetching data for: {ticker}")
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                print(f"⚠️ No data for {ticker}")
                continue
            revenue = None
            try:
                fin = stock.financials
                if "Total Revenue" in fin.index and not fin.loc["Total Revenue"].empty:
                    revenue = fin.loc["Total Revenue"].iloc[0]
            except Exception as e:
                print(f"⚠️ Revenue fetch error for {ticker}: {e}")

            all_data[ticker] = {'history': hist, 'revenue': revenue}
        except Exception as e:
            print(f"❌ Failed to fetch {ticker}: {e}")
    return all_data

def create_interactive_plotly_dashboard(data, group_name, time_period="5y"):
    closing_prices = pd.concat([d['history']['Close'] for d in data.values()], axis=1)
    closing_prices.columns = data.keys()

    melted_prices = closing_prices.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Close')

    fig1 = px.line(closing_prices, title=f"📈 Price Trend Over Time ({group_name})")
    fig1.update_layout(title_font_size=20, template="plotly_white")

    fig2 = px.box(melted_prices, x='Ticker', y='Close', color='Ticker',
                  title="📦 Stock Price Distribution", template="plotly_white")

    revenues = {k: v['revenue'] for k, v in data.items() if v['revenue'] is not None}
    if revenues:
        fig3 = px.bar(x=list(revenues.keys()), y=list(revenues.values()),
                     labels={'x': 'Ticker', 'y': 'Revenue'},
                     title="💰 Latest Reported Revenue", template="plotly_white")
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="No Revenue Data Available",
                            xref="paper", yref="paper",
                            x=0.5, y=0.5, showarrow=False)
        fig3.update_layout(title="💰 Latest Reported Revenue", template="plotly_white")

    returns = closing_prices.pct_change().mean().sort_values()
    fig4 = px.bar(x=returns.index, y=returns.values,
                  labels={'x': 'Ticker', 'y': 'Avg Daily Return'},
                  title="📉 Average Daily Returns", template="plotly_white")

    return [fig1, fig2, fig3, fig4]

def save_plotly_figures_as_html(figures, group_name, time_period):
    styles = """
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f8; padding: 20px; }
        h1 { text-align: center; color: #003366; }
        .chart-container { margin-bottom: 50px; border: 1px solid #ccc; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
    """
    combined_html = "".join([f'<div class="chart-container">{fig.to_html(full_html=False, include_plotlyjs="cdn")}</div>' for fig in figures])
    full_html = f"""
    <html>
    <head>
        <title>{group_name} Analysis ({time_period})</title>
        {styles}
    </head>
    <body>
        <h1>{group_name} Interactive Financial Dashboard ({time_period})</h1>
        {combined_html}
    </body>
    </html>
    """

    buffer = io.BytesIO(full_html.encode('utf-8'))
    filename = f"{group_name}_interactive_dashboard_{time_period}.html"

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_DEFAULT_REGION
        )
        s3.upload_fileobj(
            buffer,
            AWS_BUCKET_NAME,
            filename,
            ExtraArgs={"ContentType": "text/html"}
        )
        print(f"✅ Dashboard uploaded to S3: s3://{AWS_BUCKET_NAME}/{filename}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        with open(filename, "wb") as f:
            f.write(buffer.getbuffer())
        print(f"✅ Saved locally as {filename}")

if __name__ == "__main__":
    print("📊 Fetching financial data for US Banks...")
    time_period = "5y"
    data_us = get_financial_data(TICKER_GROUPS["US Banks"], period=time_period)
    if data_us:
        figs_us = create_interactive_plotly_dashboard(data_us, "US Banks", time_period)
        save_plotly_figures_as_html(figs_us, "US Banks", time_period)

    print("📊 Fetching financial data for US Banks in India...")
    data_india = get_financial_data(TICKER_GROUPS["US Banks in India"], period=time_period)
    if data_india:
        figs_india = create_interactive_plotly_dashboard(data_india, "US Banks in India", time_period)
        save_plotly_figures_as_html(figs_india, "US Banks in India", time_period)
