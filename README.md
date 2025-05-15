# AUTO UPDATING DATA VISUALIZATION

Automated Financial Dashboard Generator

This project automates the generation of interactive financial dashboards using Python, Plotly, and AWS S3.

Key Features

Data Source: Uses the yfinance API to fetch historical stock data and financials for specified ticker groups.

Visualizations: Generates interactive line charts, box plots, revenue bars, and return analysis using Plotly.

Output: Combines all visuals into a styled HTML dashboard.

Deployment: Dashboards are uploaded to AWS S3 or saved locally for access.

Automation-Ready: Can be scheduled with cron, Airflow, or AWS Lambda + CloudWatch to refresh data and regenerate dashboards at regular intervals.


Tech Stack

Python (data handling, automation)

pandas, yfinance, plotly

boto3 for AWS S3 integration

.env config via python-dotenv
