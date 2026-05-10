# SQL Query Assistant

An AI-powered app that converts plain English questions into SQL queries and runs them live against a sample database.

Built with Python, Streamlit, and the Claude API. Uses the Northwind sample database (customers, orders, products, employees).

## Setup

1. Clone this repo
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Add your API key:
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and replace `your-api-key-here` with your actual Anthropic API key.

5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deploy

Push to GitHub, then connect the repo at [share.streamlit.io](https://share.streamlit.io). Add your `ANTHROPIC_API_KEY` as a secret in the Streamlit dashboard.

## Stack
- Python 3.12
- Streamlit
- Anthropic Claude API
- SQLite (Northwind database)
