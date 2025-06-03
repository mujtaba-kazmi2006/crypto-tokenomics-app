import tkinter as tk
from tkinter import ttk, messagebox
import requests
import numpy as np
from fuzzywuzzy import process

# Function to fetch historical prices
def fetch_historical_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=365"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        prices = [p[1] for p in data["prices"]]
        return prices
    except:
        return None

# Function to calculate CAGR and volatility
def calculate_cagr_and_volatility(prices):
    try:
        returns = [np.log(prices[i+1] / prices[i]) for i in range(len(prices)-1)]
        avg_daily_return = np.mean(returns)
        daily_volatility = np.std(returns)

        trading_days = 365
        annual_return = np.exp(avg_daily_return * trading_days) - 1
        annual_volatility = daily_volatility * np.sqrt(trading_days)

        conservative_return = annual_return * 0.5
        return annual_return, annual_volatility, conservative_return
    except:
        return None, None, None

# Function to suggest similar tokens
def suggest_similar_tokens(user_input):
    try:
        res = requests.get("https://api.coingecko.com/api/v3/coins/list")
        coin_list = res.json()
        coin_ids = [coin['id'] for coin in coin_list]
        best_matches = process.extract(user_input.lower(), coin_ids, limit=5)
        return [match[0] for match in best_matches if match[1] > 60]
    except:
        return []

# Fetch token data and calculate relevant information
def fetch_token_data(coin_id, investment_amount):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id.lower().strip()}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        market = data["market_data"]

        circulating = market.get("circulating_supply", 0)
        total = market.get("total_supply", 0)
        price = market.get("current_price", {}).get("usd", 0)
        mcap = market.get("market_cap", {}).get("usd", 0)
        fdv = total * price if total else 0
        circ_percent = (circulating / total) * 100 if total else None
        fdv_mcap_ratio = (fdv / mcap) if mcap else None

        healthy = "✅ This coin seems healthy!" if circ_percent and circ_percent > 50 and fdv_mcap_ratio and fdv_mcap_ratio < 2 else "⚠️ Warning: This coin might be risky or inflated."

        prices = fetch_historical_prices(coin_id)
        if not prices:
            return None
        cagr, volatility, conservative_cagr = calculate_cagr_and_volatility(prices)

        expected_yearly_return = investment_amount * conservative_cagr
        expected_monthly_return = expected_yearly_return / 12

        # Format outputs
        price_str = f"${price:,.6f}"
        mcap_str = f"${mcap / 1e9:,.2f}B"
        total_str = f"{total / 1e6:,.2f}M"
        circulating_str = f"{circulating / 1e6:,.2f}M"
        fdv_str = f"${fdv / 1e9:,.2f}B"
        fdv_mcap_ratio_str = f"{fdv_mcap_ratio:,.2f}" if fdv_mcap_ratio else "N/A"
        cagr_str = f"{cagr * 100:,.2f}%" if cagr else "N/A"
        volatility_str = f"{volatility * 100:,.2f}%" if volatility else "N/A"
        conservative_cagr_str = f"{conservative_cagr * 100:,.2f}%" if conservative_cagr else "N/A"
        expected_monthly_return_str = f"${expected_monthly_return:,.2f}" if expected_monthly_return else "N/A"
        expected_yearly_return_str = f"${expected_yearly_return:,.2f}" if expected_yearly_return else "N/A"

        return {
            "Coin Name & Symbol": f"{data['name']} ({data['symbol'].upper()})",
            "Current Price ($)": price_str,
            "Market Cap (B)": mcap_str + " — The value of all coins in the market",
            "Total Supply (M)": total_str + " — Maximum possible number of coins",
            "Circulating Supply (M)": circulating_str + " — Coins that are currently in circulation",
            "Circulating Supply %": f"{circ_percent:,.2f}%" if circ_percent else "N/A",
            "FDV (B)": fdv_str + " — What the coin could be worth if all coins were unlocked",
            "FDV/Market Cap Ratio": fdv_mcap_ratio_str + " — The lower this ratio, the better",
            "Historical Annual Return (CAGR)": cagr_str + " — This is how much the coin has grown over the past year",
            "Annual Volatility": volatility_str + " — How much the coin's price fluctuates",
            "Realistic Yearly Return (50% of CAGR)": conservative_cagr_str + " — A safer, more realistic return",
            "Expected Monthly Return ($)": expected_monthly_return_str + " — How much you could make per month",
            "Expected Yearly Return ($)": expected_yearly_return_str + " — How much you could make per year",
            "Should I Invest?": healthy
        }
    except requests.exceptions.RequestException:
        return None

# Run check from GUI
def run_check():
    coin_id = entry_coin.get().strip()
    try:
        investment = float(entry_amount.get())
        if investment <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid positive investment amount in USD.")
        return

    data = fetch_token_data(coin_id, investment)

    for row in tree.get_children():
        tree.delete(row)

    if data:
        for k, v in data.items():
            tree.insert('', 'end', values=(k, v))
    else:
        suggestions = suggest_similar_tokens(coin_id)
        if suggestions:
            message = "Coin not found. Did you mean:\n\n" + "\n".join(suggestions)
        else:
            message = "Coin not found, and no similar coins were detected. Please check the spelling or try another name."
        messagebox.showerror("Coin Not Found", message)

# GUI setup
root = tk.Tk()
root.title("💰 Crypto Tokenomics & Investment Forecast By Mujtaba Kazmi")
root.geometry("900x650")
root.configure(bg="#f8f9fa")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview",
                background="#ffffff",
                foreground="#333333",
                rowheight=40,
                fieldbackground="#ffffff",
                font=('Roboto', 12),
                borderwidth=1, relief="solid")
style.configure("Treeview.Heading", background="#007bff", foreground="white", font=('Roboto', 13, 'bold'))

tk.Label(root, text="Enter CoinGecko Coin ID (e.g. 'solana', 'ethereum', 'bitcoin')", bg="#f8f9fa", fg="#007bff", font=("Roboto", 14)).pack(pady=(15, 5))
entry_coin = tk.Entry(root, width=30, font=("Roboto", 14), bd=2, relief="solid")
entry_coin.pack()

tk.Label(root, text="Enter Investment Amount in USD ($)", bg="#f8f9fa", fg="#007bff", font=("Roboto", 14)).pack(pady=(15, 5))
entry_amount = tk.Entry(root, width=30, font=("Roboto", 14), bd=2, relief="solid")
entry_amount.pack()

button = ttk.Button(root, text="🔍 Analyze Token & Forecast", command=run_check, style="TButton")
button.pack(pady=15)

tree = ttk.Treeview(root, columns=("Metric", "Value & Explanation"), show='headings', height=12)
tree.heading("Metric", text="Metric")
tree.heading("Value & Explanation", text="Value & Explanation")
tree.column("Metric", anchor="w", width=400)
tree.column("Value & Explanation", anchor="w", width=440)
tree.pack(pady=10, fill="both", expand=True)

root.mainloop()
