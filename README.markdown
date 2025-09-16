# Ultimate Stock Trader 🚀

Welcome to **Ultimate Stock Trader**, an advanced stock trading simulation and analysis tool built with Python. This project is designed exclusively for the **Indian Stock Exchange**, leveraging real-time data from **NIFTY 50** stocks via Yahoo Finance. It offers sophisticated trading features and interactive visualizations, making it an excellent platform for practicing strategies and exploring the Indian market.

## Features ✨

- **Real-Time Market Data**: Fetch live prices and performance metrics for NIFTY 50 stocks.
- **Advanced Trading Options**: Execute market buys/sells, limit orders, percentage-based sells, and conditional sells based on technical indicators.
- **Risk Management Tools**: Set stop-loss orders (fixed and trailing) to protect your investments automatically.
- **Professional Charts**: Visualize stock performance with candlestick charts, multiple Simple Moving Averages (SMA), and technical analysis indicators.
- **Portfolio Management**: Track your holdings, calculate net worth, and analyze profit/loss with detailed breakdowns.
- **Leaderboards & Challenges**: Compete with others in a trading challenge mode and view top traders.
- **Admin Tools**: Manage users, reset data, and monitor system stats (for admins only).
- **New Feature - Top 10 Performers**: View the top 10 gainers and losers of the day with the `top10` command for quick market insights.

## Installation 📦

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/ultimate-stock-trader.git
   cd ultimate-stock-trader
   ```

2. **Install Dependencies**: Ensure you have Python 3.8+ installed. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Data Files**: The application creates `users.json`, `leaderboard.json`, and `pending_orders.json` automatically. Run the script once to initialize them.

4. **Run the Application**:

   ```bash
   python main.py
   ```

## Usage 🚀

- Start the app and log in with a username.
- Use commands like:
  - `prices <symbol>` - View live prices or specific stock details (e.g., `prices RELIANCE`).
  - `top10` - Display top 10 gainers and losers.
  - `buy <symbol> <shares>` - Purchase stocks (e.g., `buy INFY 10`).
  - `stoploss <symbol> <shares> <price>` - Set a stop-loss (e.g., `stoploss TCS 5 4000`).
  - `graph <symbol> [period]` - Analyze stock with charts (e.g., `graph HDFCBANK 3mo`).
  - `portfolio` - Check your holdings.
  - `help` - View all commands.

### Example Commands

Here are some pre-written examples to get you started:

- Check market prices: `prices`
- Buy 15 shares of Reliance: `buy RELIANCE 15`
- Set a trailing stop-loss for 5 shares of Infosys at 5% trailing: `trailstop INFY 5 5`
- View detailed chart for Tata Motors over 1 month: `graph TATAMOTORS 1mo`
- Sell 20% of your HDFC Bank holdings: `sellpct HDFCBANK 20`

## Example Images 📸

Add screenshots or visualizations here to showcase the tool:

- [ ] Top 10 Gainers/Losers Table
      (![Top 10 Gainers](images/T10.png))


- [ ] Candlestick Chart with SMA Overlays
      (![Top 10 Gainers](images/CC.png))

      
- [ ] Portfolio Summary
      (![Top 10 Gainers](images/PS.png))


- [ ] Suggestion
      (![Top 10 Gainers](images/PS.png))


## New Features in This Update 🌟

- **Top 10 Command**: Added `top10` to showcase the day's top 10 gainers and losers with ranked lists and market summary.
- **Enhanced Visuals**: Improved terminal UI with colored tables, panels, and progress bars for a richer experience.
- **Advanced Analysis**: Integrated multi-SMA technical analysis and risk management suggestions in graphs.

## Requirements 📋

- Python 3.8+
- `yfinance` for market data
- `mplfinance` for charting
- `rich` for terminal formatting
- `matplotlib` for visualizations

Install via `requirements.txt` or individually with `pip`.

## Contributing 🤝

Contributions are welcome! Please fork the repository and submit pull requests. Follow these steps:

1. Fork the repo.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License 📜

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments 🙏

- Thanks to the open-source community for tools like `yfinance` and `rich`.
- Inspired by real-world trading platforms and educational simulations.
