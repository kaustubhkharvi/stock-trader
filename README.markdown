# Ultimate Stock Trader 🚀

Welcome to **Ultimate Stock Trader**, an advanced stock trading simulation and analysis tool built with Python. This project combines real-time market data, sophisticated trading features, and interactive visualizations to provide an immersive trading experience. Whether you're a beginner or an experienced trader, this tool offers a robust platform to practice strategies and explore the stock market.

## Features ✨

- **Real-Time Market Data**: Fetch live prices and performance metrics for NIFTY 50 stocks using Yahoo Finance.
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

2. **Install Dependencies**:
   Ensure you have Python 3.8+ installed. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Data Files**:
   The application creates `users.json`, `leaderboard.json`, and `pending_orders.json` automatically. Run the script once to initialize them.

4. **Run the Application**:
   ```bash
   python main.py
   ```

## Usage 🚀

- Start the app and log in with a username.
- Use commands like:
  - `prices [symbol]` - View live prices or specific stock details.
  - `top10` - Display top 10 gainers and losers.
  - `buy <symbol> <shares>` - Purchase stocks.
  - `stoploss <symbol> <shares> <price>` - Set a stop-loss.
  - `graph <symbol> [period]` - Analyze stock with charts.
  - `portfolio` - Check your holdings.
  - `help` - View all commands.

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

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Thanks to the open-source community for tools like `yfinance` and `rich`.
- Inspired by real-world trading platforms and educational simulations.