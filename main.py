#!/usr/bin/env python3

import json
import os
import random
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint
from rich.align import Align
from rich.layout import Layout
from rich.columns import Columns
from rich.rule import Rule
from rich.text import Text
from rich.tree import Tree
from candlestick_chart import Candle, Chart
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
import tempfile

console = Console()

# Data files
USERS_FILE = 'users.json'
LEADERBOARD_FILE = 'leaderboard.json'
ORDERS_FILE = 'pending_orders.json'

# NIFTY 50 symbols for tracking top performers
SYMBOLS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BPCL.NS', 'BHARTIARTL.NS',
    'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS',
    'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS',
    'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS',
    'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SUNPHARMA.NS',
    'TCS.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS',
    'TITAN.NS', 'TRENT.NS', 'ULTRACEMCO.NS', 'UPL.NS', 'WIPRO.NS'
]

# For challenge mode (mock data)
INITIAL_STOCKS = [
    {'symbol': s[:-3], 'price': 150.0, 'vol': 0.02, 'last_price': 150.0} for s in SYMBOLS[:10]
]

EVENTS = [
    {'name': '🚀 Market Boom! All stocks rise.', 'effect': 1.1, 'prob': 0.02, 'target': 'all'},
    {'name': '💥 Market Crash! All stocks fall.', 'effect': 0.9, 'prob': 0.02, 'target': 'all'},
    {'name': '⚡ Tech Boost for INFY!', 'effect': 1.15, 'prob': 0.03, 'target': 'INFY'},
    {'name': '⚠️  Regulatory Issue for RELIANCE.', 'effect': 0.85, 'prob': 0.03, 'target': 'RELIANCE'},
]

# Original clean ASCII logo
ASCII_LOGO = """
 ____  _             _    _____              _             ____            
/ ___|| |_ ___   ___| | _|_   _| __ __ _  __| | ___ _ __  |  _ \\ _ __ ___  
\\___ \\| __/ _ \\ / __| |/ / | || '__/ _` |/ _` |/ _ \\ '__| | |_) | '__/ _ \\ 
 ___) | || (_) | (__|   <  | || | | (_| | (_| |  __/ |    |  __/| | | (_) |
|____/ \\__\\___/ \\___|_|\_\\ |_| |_|  \\__,_|\\__,_|\\___|_|    |_|   |_|  \\___/  

🚀 ULTIMATE EDITION - Advanced Trading & Risk Management 🚀
✨ Stop-Loss • Limit Orders • Professional Charts • Admin Tools ✨
"""

def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if file == LEADERBOARD_FILE:
                        for user, score in list(data.items()):
                            if not isinstance(score, (int, float)):
                                console.print(f"[red]Invalid score for {user} in {file}. Resetting to 0.0.[/red]")
                                data[user] = 0.0
                    elif file == USERS_FILE:
                        for user, info in list(data.items()):
                            if not isinstance(info, dict) or 'balance' not in info or 'portfolio' not in info:
                                console.print(f"[red]Invalid data for {user} in {file}. Resetting.[/red]")
                                data[user] = {'balance': 10000.0, 'portfolio': {}, 'stop_losses': {}}
                            if 'stop_losses' not in info:
                                data[user]['stop_losses'] = {}
                return data
        except json.JSONDecodeError:
            console.print(f"[red]Error loading {file}. Creating new data.[/red]")
            return default
    return default

def save_data(file, data):
    try:
        with open(file, 'w') as f:
            json.dump(data, f, indent=2)
    except PermissionError:
        console.print(f"[red]Permission denied while saving {file}. Check file permissions.[/red]")
    except Exception as e:
        console.print(f"[red]Error saving {file}: {e}[/red]")

def enhanced_loading_animation(message, duration=1.0):
    """Enhanced loading animation with progress bar"""
    progress = Progress(
        SpinnerColumn("dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
        transient=True
    )
    task = progress.add_task(description=message, total=100)
    with Live(progress, console=console, refresh_per_second=20):
        for i in range(100):
            time.sleep(duration/100)
            progress.update(task, advance=1)

def create_status_panel(user, stocks):
    """Create a beautiful status panel with user info"""
    net_worth = calculate_net_worth(user, stocks)
    portfolio_value = net_worth - user['balance']
    
    # Status table
    status_table = Table.grid(padding=1)
    status_table.add_column(style="cyan", justify="right")
    status_table.add_column(style="white")
    
    status_table.add_row("💰 Cash Balance:", f"₹{user['balance']:,.2f}")
    status_table.add_row("📊 Portfolio Value:", f"₹{portfolio_value:,.2f}")
    status_table.add_row("💎 Net Worth:", f"₹{net_worth:,.2f}")
    status_table.add_row("📈 Active Holdings:", f"{len(user['portfolio'])} stocks")
    status_table.add_row("🛡️  Stop Losses:", f"{len(user.get('stop_losses', {}))} orders")
    
    return Panel(status_table, title="💼 Account Status", border_style="green")

def fetch_prices():
    stocks = []
    nse_stocks = SYMBOLS
    for symbol in nse_stocks:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else price
                change = ((price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
                stocks.append({'symbol': symbol.replace('.NS', ''), 'price': price, 'change': change})
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to fetch {symbol}: {str(e)}[/yellow]")
            continue
    return stocks if stocks else []

def fetch_single_price(sym):
    try:
        ticker = yf.Ticker(f"{sym}.NS")
        data = ticker.history(period="2d", auto_adjust=False)
        if len(data) < 2:
            return None
        prev_close = data['Close'].iloc[-2]
        current = data['Close'].iloc[-1]
        change = ((current - prev_close) / prev_close * 100) if prev_close != 0 else 0
        return {
            'symbol': sym,
            'price': current,
            'last_price': prev_close,
            'change': change
        }
    except Exception as e:
        console.print(f"[red]Error fetching {sym}: {e}[/red]")
        return None

def fetch_historical_data(sym, period):
    try:
        ticker = yf.Ticker(f"{sym}.NS")
        data = ticker.history(period=period)
        if data.empty:
            raise Exception("No historical data available")
        return data
    except Exception as e:
        console.print(f"[red]Error fetching historical data for {sym}: {e}[/red]")
        return None

def calculate_sma(data, window):
    """Calculate Simple Moving Average for given window period"""
    return data['Close'].rolling(window=window, min_periods=1).mean()

def show_ultimate_graph(sym, period="3mo"):
    """Ultimate graph with SMA lines, enhanced visuals and risk indicators"""
    data = fetch_historical_data(sym, period)
    if data is None or data.empty:
        console.print("[red]No data available for graph.[/red]")
        return
    
    console.print(Panel(f"🎯 ULTIMATE Technical Analysis for {sym} over {period}", title="📈 Advanced Market Analysis", style="bold blue"))
    
    try:
        # Calculate multiple SMAs and technical indicators
        sma_5 = calculate_sma(data, 5)
        sma_20 = calculate_sma(data, 20)
        sma_50 = calculate_sma(data, 50)
        sma_200 = calculate_sma(data, 200) if len(data) >= 200 else sma_50
        
        # Get latest values
        current_price = data['Close'].iloc[-1]
        latest_sma_5 = sma_5.iloc[-1]
        latest_sma_20 = sma_20.iloc[-1]
        latest_sma_50 = sma_50.iloc[-1]
        latest_sma_200 = sma_200.iloc[-1]
        
        # Calculate volatility
        volatility = data['Close'].pct_change().std() * 100
        
        console.print("[cyan]📊 Generating professional chart with multiple SMA overlays...[/cyan]")
        
        # Create advanced chart with multiple SMAs
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            chart_path = tmp_file.name
        
        # Advanced styling
        mc = mpf.make_marketcolors(up='#00ff88', down='#ff4444', edge='inherit',
                                   wick={'up':'#00cc66', 'down':'#cc3333'},
                                   volume='#888888')
        
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True,
                               facecolor='#0d1117', figcolor='#161b22')
        
        # Plot with multiple SMA lines
        mpf.plot(data, 
                type='candle',
                mav=(5, 20, 50, 200),
                volume=True,
                style=s,
                title=f'{sym} - Advanced Technical Analysis',
                ylabel='Price (₹)',
                savefig=dict(fname=chart_path, dpi=150, bbox_inches='tight'),
                figsize=(16, 10))
        
        console.print(f"[green]✅ Professional chart saved: {chart_path}[/green]")
        
        # Show terminal chart for quick reference
        console.print("\n[cyan]📊 Quick Terminal View:[/cyan]")
        candles = [Candle(open=row.Open, high=row.High, low=row.Low, close=row.Close) for row in data.itertuples()]
        chart = Chart(candles, title=f"{sym} Live Chart")
        chart.set_bear_color(255, 68, 68)
        chart.set_bull_color(0, 255, 136)
        chart.set_volume_pane_enabled(False)
        chart.draw()
        
        # Ultimate Technical Analysis Table
        analysis_table = Table(title="🎯 ULTIMATE Technical Analysis", style="bold cyan", expand=True)
        analysis_table.add_column("Indicator", style="cyan", width=15)
        analysis_table.add_column("Value", justify="right", style="green", width=12)
        analysis_table.add_column("Signal", justify="center", width=15)
        analysis_table.add_column("Strength", justify="center", width=12)
        analysis_table.add_column("Recommendation", justify="center", width=15)
        
        # Calculate comprehensive signals
        signals = []
        
        # SMA 5 (Ultra Short-term)
        sma5_diff = ((current_price - latest_sma_5) / latest_sma_5) * 100
        sma5_signal = "🟢 Bullish" if current_price > latest_sma_5 else "🔴 Bearish"
        sma5_strength = "🔥 Strong" if abs(sma5_diff) > 2 else "⚡ Moderate" if abs(sma5_diff) > 0.5 else "💫 Weak"
        sma5_rec = "📈 BUY" if current_price > latest_sma_5 and sma5_diff > 1 else "📉 SELL" if current_price < latest_sma_5 and sma5_diff < -1 else "⏸️  HOLD"
        
        # SMA 20 (Short-term)
        sma20_diff = ((current_price - latest_sma_20) / latest_sma_20) * 100
        sma20_signal = "🟢 Bullish" if current_price > latest_sma_20 else "🔴 Bearish"
        sma20_strength = "🔥 Strong" if abs(sma20_diff) > 3 else "⚡ Moderate" if abs(sma20_diff) > 1 else "💫 Weak"
        sma20_rec = "📈 BUY" if current_price > latest_sma_20 and sma20_diff > 2 else "📉 SELL" if current_price < latest_sma_20 and sma20_diff < -2 else "⏸️  HOLD"
        
        # SMA 50 (Medium-term)
        sma50_diff = ((current_price - latest_sma_50) / latest_sma_50) * 100
        sma50_signal = "🟢 Bullish" if current_price > latest_sma_50 else "🔴 Bearish"
        sma50_strength = "🔥 Strong" if abs(sma50_diff) > 5 else "⚡ Moderate" if abs(sma50_diff) > 2 else "💫 Weak"
        sma50_rec = "📈 BUY" if current_price > latest_sma_50 and sma50_diff > 3 else "📉 SELL" if current_price < latest_sma_50 and sma50_diff < -3 else "⏸️  HOLD"
        
        # SMA 200 (Long-term trend)
        sma200_diff = ((current_price - latest_sma_200) / latest_sma_200) * 100
        sma200_signal = "🟢 Bull Market" if current_price > latest_sma_200 else "🔴 Bear Market"
        sma200_strength = "🔥 Strong" if abs(sma200_diff) > 10 else "⚡ Moderate" if abs(sma200_diff) > 5 else "💫 Weak"
        sma200_rec = "📈 INVEST" if current_price > latest_sma_200 and sma200_diff > 5 else "📉 AVOID" if current_price < latest_sma_200 and sma200_diff < -5 else "⏸️  WATCH"
        
        # Golden Cross / Death Cross
        cross_signal = "🚀 Golden Cross" if latest_sma_20 > latest_sma_50 else "💀 Death Cross"
        cross_strength = "🔥 Strong" if abs((latest_sma_20 - latest_sma_50) / latest_sma_50 * 100) > 3 else "⚡ Moderate"
        
        analysis_table.add_row("💰 Current Price", f"₹{current_price:.2f}", "", "", "")
        analysis_table.add_row("⚡ SMA 5", f"₹{latest_sma_5:.2f}", sma5_signal, sma5_strength, sma5_rec)
        analysis_table.add_row("📊 SMA 20", f"₹{latest_sma_20:.2f}", sma20_signal, sma20_strength, sma20_rec)
        analysis_table.add_row("📈 SMA 50", f"₹{latest_sma_50:.2f}", sma50_signal, sma50_strength, sma50_rec)
        analysis_table.add_row("🎯 SMA 200", f"₹{latest_sma_200:.2f}", sma200_signal, sma200_strength, sma200_rec)
        analysis_table.add_row("⚔️  Trend Signal", f"{latest_sma_20/latest_sma_50:.3f}", cross_signal, cross_strength, "")
        analysis_table.add_row("📊 Volatility", f"{volatility:.1f}%", "🔥 High" if volatility > 3 else "⚡ Medium" if volatility > 1.5 else "💫 Low", "", "")
        
        console.print(Panel(analysis_table, title="🎯 Professional Technical Analysis", border_style="bright_cyan"))
        
        # Risk Management Suggestions
        risk_table = Table(title="🛡️  Risk Management Suggestions", style="bold yellow")
        risk_table.add_column("Risk Level", style="red")
        risk_table.add_column("Stop Loss", style="yellow")
        risk_table.add_column("Take Profit", style="green")
        risk_table.add_column("Position Size", style="cyan")
        
        # Calculate risk levels
        conservative_sl = current_price * 0.95  # 5% stop loss
        moderate_sl = current_price * 0.92     # 8% stop loss  
        aggressive_sl = current_price * 0.88   # 12% stop loss
        
        conservative_tp = current_price * 1.10  # 10% take profit
        moderate_tp = current_price * 1.15     # 15% take profit
        aggressive_tp = current_price * 1.25   # 25% take profit
        
        risk_table.add_row("🟢 Conservative", f"₹{conservative_sl:.2f}", f"₹{conservative_tp:.2f}", "25% of portfolio")
        risk_table.add_row("🟡 Moderate", f"₹{moderate_sl:.2f}", f"₹{moderate_tp:.2f}", "15% of portfolio")
        risk_table.add_row("🔴 Aggressive", f"₹{aggressive_sl:.2f}", f"₹{aggressive_tp:.2f}", "10% of portfolio")
        
        console.print(Panel(risk_table, title="💡 Smart Trading Suggestions", border_style="yellow"))
        
    except Exception as e:
        console.print(f"[red]Error creating ultimate chart: {e}[/red]")
        console.print("[yellow]Falling back to simple chart...[/yellow]")

def calculate_net_worth(user, stocks):
    total_value = 0
    for sym, data in user['portfolio'].items():
        shares = data.get('shares', 0)
        stock = next((s for s in stocks if s['symbol'] == sym), None)
        if stock:
            total_value += shares * stock['price']
        else:
            temp_stock = fetch_single_price(sym)
            if temp_stock:
                total_value += shares * temp_stock['price']
    return user['balance'] + total_value

def check_stop_losses(user, stocks):
    """Check and execute stop-loss orders automatically (including trailing stops)"""
    executed_orders = []
    stop_losses = user.get('stop_losses', {})
    
    for sym, stop_data in list(stop_losses.items()):
        if sym not in user['portfolio']:
            del stop_losses[sym]
            continue
            
        # Get current price
        stock = next((s for s in stocks if s['symbol'] == sym), None)
        if not stock:
            stock = fetch_single_price(sym)
        
        if not stock:
            continue
            
        current_price = stock['price']
        stop_price = stop_data['price']
        shares = stop_data['shares']
        is_trailing = stop_data.get('trailing', False)
        
        # Handle trailing stop logic
        if is_trailing:
            trailing_percent = stop_data.get('trailing_percent', 5)
            highest_price = stop_data.get('highest_price', current_price)
            
            # Update highest price if current price is higher
            if current_price > highest_price:
                highest_price = current_price
                stop_data['highest_price'] = highest_price
                # Adjust stop price based on new high
                new_stop_price = highest_price * (1 - trailing_percent / 100)
                stop_data['price'] = new_stop_price
                stop_price = new_stop_price
        
        # Execute stop loss if price hits or goes below stop price
        if current_price <= stop_price:
            # Execute the stop loss
            revenue = current_price * shares
            user['balance'] += revenue
            
            # Update portfolio
            if shares >= user['portfolio'][sym]['shares']:
                del user['portfolio'][sym]
            else:
                user['portfolio'][sym]['shares'] -= shares
            
            # Remove the stop loss order
            del stop_losses[sym]
            
            stop_type = "🚂 TRAILING STOP" if is_trailing else "🛡️  STOP LOSS"
            
            executed_orders.append({
                'symbol': sym,
                'shares': shares,
                'price': current_price,
                'revenue': revenue,
                'stop_price': stop_price,
                'trailing': is_trailing
            })
            
            console.print(Panel(
                f"{stop_type} [red]EXECUTED![/red]\n"
                f"Symbol: {sym}\n"
                f"Shares Sold: {shares}\n"
                f"Stop Price: ₹{stop_price:.2f}\n"
                f"Execution Price: ₹{current_price:.2f}\n"
                f"Revenue: ₹{revenue:.2f}",
                title="🚨 Stop Loss Alert",
                border_style="red"
            ))
    
    return executed_orders

def process_limit_orders(pending_orders, stocks, users):
    """Process limit orders and execute when price conditions are met"""
    executed_orders = []
    
    for order_id, order in list(pending_orders.items()):
        sym = order['symbol']
        target_price = order['price']
        shares = order['shares']
        order_type = order['type']  # 'buy' or 'sell'
        username = order['user']
        
        if username not in users:
            del pending_orders[order_id]
            continue
            
        user = users[username]
        
        # Get current price
        stock = next((s for s in stocks if s['symbol'] == sym), None)
        if not stock:
            stock = fetch_single_price(sym)
        
        if not stock:
            continue
            
        current_price = stock['price']
        
        # Check if order should be executed
        should_execute = False
        if order_type == 'buy' and current_price <= target_price:
            should_execute = True
        elif order_type == 'sell' and current_price >= target_price:
            should_execute = True
        
        if should_execute:
            if order_type == 'buy':
                cost = current_price * shares
                if user['balance'] >= cost:
                    # Execute buy order
                    user['balance'] -= cost
                    if sym not in user['portfolio']:
                        user['portfolio'][sym] = {'shares': shares, 'avg_cost': current_price}
                    else:
                        old_data = user['portfolio'][sym]
                        old_shares = old_data['shares']
                        old_avg = old_data['avg_cost']
                        new_shares = old_shares + shares
                        new_avg = (old_avg * old_shares + current_price * shares) / new_shares
                        user['portfolio'][sym] = {'shares': new_shares, 'avg_cost': new_avg}
                    
                    executed_orders.append({
                        'type': 'buy',
                        'symbol': sym,
                        'shares': shares,
                        'target_price': target_price,
                        'execution_price': current_price,
                        'cost': cost,
                        'user': username
                    })
            
            elif order_type == 'sell':
                if sym in user['portfolio'] and user['portfolio'][sym]['shares'] >= shares:
                    # Execute sell order
                    revenue = current_price * shares
                    user['balance'] += revenue
                    user['portfolio'][sym]['shares'] -= shares
                    if user['portfolio'][sym]['shares'] == 0:
                        del user['portfolio'][sym]
                    
                    executed_orders.append({
                        'type': 'sell',
                        'symbol': sym,
                        'shares': shares,
                        'target_price': target_price,
                        'execution_price': current_price,
                        'revenue': revenue,
                        'user': username
                    })
            
            # Remove executed order
            del pending_orders[order_id]
    
    return executed_orders

def show_enhanced_prices(stocks, specific_sym=None):
    """Enhanced price display with advanced formatting"""
    enhanced_loading_animation("Loading market data...")
    
    if specific_sym:
        stock = fetch_single_price(specific_sym)
        if stock:
            # Create detailed single stock view
            price_table = Table(title=f"📊 {specific_sym} Live Price", style="bold magenta", expand=True)
            price_table.add_column("Metric", style="cyan", width=15)
            price_table.add_column("Value", justify="right", style="green", width=12)
            price_table.add_column("Status", justify="center", width=15)
            
            change_str = f"{stock['change']:+.2f}%"
            trend_emoji = "🚀" if stock['change'] > 2 else "📈" if stock['change'] > 0 else "📉" if stock['change'] < 0 else "➡️"
            color = "bright_green" if stock['change'] > 0 else "bright_red" if stock['change'] < 0 else "white"
            
            price_table.add_row("💰 Current Price", f"₹{stock['price']:.2f}", "")
            price_table.add_row("📊 Previous Close", f"₹{stock['last_price']:.2f}", "")
            price_table.add_row("📈 Change", f"[{color}]{change_str}[/{color}]", f"{trend_emoji}")
            price_table.add_row("🕐 Updated", datetime.now().strftime("%H:%M:%S"), "Live")
            
            console.print(Panel(price_table, title="🎯 Live Market Data", border_style="bright_blue"))
        return

    # Enhanced market overview
    sorted_stocks = sorted(stocks, key=lambda x: x.get('change', 0), reverse=True)
    
    if not sorted_stocks:
        console.print("[red]No stock data available to display.[/red]")
        return
        
    # Split into gainers and losers
    gainers = [s for s in sorted_stocks if s.get('change', 0) > 0][:5]
    losers = [s for s in sorted_stocks if s.get('change', 0) < 0][-5:]
    
    # Create columns layout
    left_panel = Table(title="🚀 Top Gainers", style="bold green", expand=True)
    left_panel.add_column("Symbol", style="cyan")
    left_panel.add_column("Price", justify="right", style="white")
    left_panel.add_column("Change", justify="right")
    
    right_panel = Table(title="📉 Top Losers", style="bold red", expand=True)
    right_panel.add_column("Symbol", style="cyan")
    right_panel.add_column("Price", justify="right", style="white")
    right_panel.add_column("Change", justify="right")
    
    for stock in gainers:
        change_str = f"+{stock.get('change', 0):.2f}%"
        left_panel.add_row(stock.get('symbol', 'N/A'), f"₹{stock.get('price', 0):.2f}", f"[bright_green]{change_str}[/bright_green]")
    
    for stock in losers:
        change_str = f"{stock.get('change', 0):.2f}%"
        right_panel.add_row(stock.get('symbol', 'N/A'), f"₹{stock.get('price', 0):.2f}", f"[bright_red]{change_str}[/bright_red]")
    
    # Display in columns
    console.print(Columns([
        Panel(left_panel, border_style="green"),
        Panel(right_panel, border_style="red")
    ]))
    
    # Market summary
    total_stocks = len(sorted_stocks)
    gaining_stocks = len([s for s in sorted_stocks if s.get('change', 0) > 0])
    losing_stocks = len([s for s in sorted_stocks if s.get('change', 0) < 0])
    
    summary_text = f"📊 Market Summary: {gaining_stocks} gaining • {losing_stocks} declining • {total_stocks - gaining_stocks - losing_stocks} unchanged"
    console.print(Panel(summary_text, title="📈 Market Overview", style="bold blue"))

def show_top10(stocks):
    """Display the top 10 gainers and top 10 losers for the day."""
    enhanced_loading_animation("Fetching top performers...")
    
    if not stocks:
        console.print("[red]No stock data available to display top 10.[/red]")
        return
    
    # Sort stocks by percentage change
    sorted_stocks = sorted(stocks, key=lambda x: x.get('change', 0), reverse=True)
    
    # Top 10 gainers
    gainers = sorted_stocks[:10]
    gainers_table = Table(title="🚀 Top 10 Gainers", style="bold green", expand=True)
    gainers_table.add_column("Rank", style="cyan", width=5)
    gainers_table.add_column("Symbol", style="white", width=10)
    gainers_table.add_column("Price", justify="right", style="green", width=12)
    gainers_table.add_column("Change", justify="right", width=10)
    
    for rank, stock in enumerate(gainers, 1):
        change_str = f"+{stock.get('change', 0):.2f}%"
        gainers_table.add_row(str(rank), stock.get('symbol', 'N/A'), f"₹{stock.get('price', 0):.2f}", f"[bright_green]{change_str}[/bright_green]")
    
    # Top 10 losers
    losers = sorted_stocks[-10:][::-1]  # Reverse to show from least to most loss
    losers_table = Table(title="📉 Top 10 Losers", style="bold red", expand=True)
    losers_table.add_column("Rank", style="cyan", width=5)
    losers_table.add_column("Symbol", style="white", width=10)
    losers_table.add_column("Price", justify="right", style="red", width=12)
    losers_table.add_column("Change", justify="right", width=10)
    
    for rank, stock in enumerate(losers, 1):
        change_str = f"{stock.get('change', 0):.2f}%"
        losers_table.add_row(str(rank), stock.get('symbol', 'N/A'), f"₹{stock.get('price', 0):.2f}", f"[bright_red]{change_str}[/bright_red]")
    
    # Display in columns
    console.print(Columns([
        Panel(gainers_table, border_style="green"),
        Panel(losers_table, border_style="red")
    ]))
    
    # Market summary
    total_stocks = len(sorted_stocks)
    gaining_stocks = len([s for s in sorted_stocks if s.get('change', 0) > 0])
    losing_stocks = len([s for s in sorted_stocks if s.get('change', 0) < 0])
    summary_text = f"📊 Market Summary: {gaining_stocks} gaining • {losing_stocks} declining • {total_stocks - gaining_stocks - losing_stocks} unchanged"
    console.print(Panel(summary_text, title="📈 Daily Market Overview", style="bold blue"))

def set_stop_loss(user, sym, shares, stop_price, trailing=False, trailing_percent=None):
    """Set a stop-loss order for a stock (with optional trailing stop)"""
    if sym not in user['portfolio']:
        console.print("[red]❌ You don't own this stock.[/red]")
        return False
    
    available_shares = user['portfolio'][sym]['shares']
    if shares > available_shares:
        console.print(f"[red]❌ You only have {available_shares} shares of {sym}.[/red]")
        return False
    
    # Initialize stop_losses if it doesn't exist
    if 'stop_losses' not in user:
        user['stop_losses'] = {}
    
    # Get current price for trailing stop
    current_price = stop_price  # Default fallback
    if trailing and trailing_percent:
        stock = fetch_single_price(sym)
        if stock:
            current_price = stock['price']
            stop_price = current_price * (1 - trailing_percent / 100)
        else:
            console.print("[red]❌ Unable to fetch current price for trailing stop setup.[/red]")
            return False
    
    # Add/update stop loss
    user['stop_losses'][sym] = {
        'shares': shares,
        'price': stop_price,
        'set_time': datetime.now().isoformat(),
        'trailing': trailing,
        'trailing_percent': trailing_percent,
        'highest_price': current_price if trailing else None
    }
    
    stop_type = "🚂 Trailing Stop Loss" if trailing else "🛡️  Stop Loss"
    trailing_info = f"\nTrailing %: {trailing_percent}%" if trailing else ""
    
    console.print(Panel(
        f"{stop_type} set successfully!\n"
        f"Symbol: {sym}\n"
        f"Shares: {shares}\n"
        f"Stop Price: ₹{stop_price:.2f}{trailing_info}\n"
        f"Your position will be automatically sold when conditions are met",
        title="✅ Advanced Stop Loss Activated",
        border_style="green"
    ))
    return True

def advanced_sell_analysis(user, sym, stocks):
    """Provide advanced selling recommendations based on technical analysis"""
    if sym not in user['portfolio']:
        return None
    
    stock = next((s for s in stocks if s['symbol'] == sym), None)
    if not stock:
        stock = fetch_single_price(sym)
    
    if not stock:
        return None
        
    current_price = stock['price']
    user_avg_cost = user['portfolio'][sym]['avg_cost']
    profit_loss_pct = ((current_price - user_avg_cost) / user_avg_cost) * 100
    
    # Fetch historical data for technical analysis
    data = fetch_historical_data(sym, "3mo")
    if data is None or data.empty:
        return None
    
    # Calculate technical indicators
    sma_20 = calculate_sma(data, 20).iloc[-1]
    sma_50 = calculate_sma(data, 50).iloc[-1]
    
    # Analyze selling conditions
    recommendations = []
    
    # Profit taking recommendations
    if profit_loss_pct > 20:
        recommendations.append("💰 Strong profit achieved! Consider taking some profits.")
    elif profit_loss_pct > 10:
        recommendations.append("📈 Good profit level. Consider partial profit taking.")
    
    # Technical analysis recommendations
    if current_price < sma_20 < sma_50:
        recommendations.append("📉 Price below both SMAs - Consider defensive selling.")
    elif current_price < sma_20:
        recommendations.append("⚠️  Price below SMA20 - Monitor closely for exit.")
    
    # Loss cutting recommendations
    if profit_loss_pct < -10:
        recommendations.append("🔴 Significant loss! Consider stop-loss to limit damage.")
    elif profit_loss_pct < -5:
        recommendations.append("⚠️  Minor loss. Set stop-loss as precaution.")
    
    return {
        'current_price': current_price,
        'avg_cost': user_avg_cost,
        'profit_loss_pct': profit_loss_pct,
        'recommendations': recommendations,
        'sma_20': sma_20,
        'sma_50': sma_50
    }

def sell_percentage(user, sym, percentage, stocks):
    """Sell a percentage of holdings in a stock"""
    if sym not in user['portfolio']:
        console.print("[red]❌ You don't own this stock.[/red]")
        return False
    
    if not (0 < percentage <= 100):
        console.print("[red]❌ Percentage must be between 0 and 100.[/red]")
        return False
    
    total_shares = user['portfolio'][sym]['shares']
    shares_to_sell = int(total_shares * percentage / 100)
    
    if shares_to_sell == 0:
        console.print("[red]❌ Calculated shares to sell is 0. Try a higher percentage.[/red]")
        return False
    
    # Get current price
    stock = next((s for s in stocks if s['symbol'] == sym), None)
    if not stock:
        stock = fetch_single_price(sym)
    
    if not stock:
        console.print("[red]❌ Unable to fetch current price.[/red]")
        return False
    
    current_price = stock['price']
    revenue = current_price * shares_to_sell
    
    console.print(Panel(
        f"📊 Selling {percentage}% of your {sym} position\n"
        f"Total Shares: {total_shares}\n"
        f"Shares to Sell: {shares_to_sell}\n"
        f"Current Price: ₹{current_price:.2f}\n"
        f"Estimated Revenue: ₹{revenue:.2f}",
        title="💰 Percentage Sell Order",
        border_style="yellow"
    ))
    
    confirm = console.input(f"[bold]Confirm sell {percentage}% ({shares_to_sell} shares) of {sym}? (yes/no): [/bold]").strip().lower()
    
    if confirm == 'yes':
        # Execute the sale
        user['balance'] += revenue
        user['portfolio'][sym]['shares'] -= shares_to_sell
        
        if user['portfolio'][sym]['shares'] == 0:
            del user['portfolio'][sym]
        
        console.print(Panel(
            f"✅ Successfully sold {shares_to_sell} shares ({percentage}%) of {sym}\n"
            f"Revenue: ₹{revenue:.2f}\n"
            f"New Balance: ₹{user['balance']:.2f}",
            title="🎉 Sale Completed",
            border_style="green"
        ))
        return True
    else:
        console.print("[yellow]Sale cancelled.[/yellow]")
        return False

def conditional_sell(user, pending_orders, username, sym, shares, conditions):
    """Set up conditional sell orders based on technical conditions"""
    condition_type = conditions.get('type', '')
    
    if condition_type == 'sma_cross':
        # Sell when price crosses below SMA
        sma_period = conditions.get('sma_period', 20)
        order_id = f"{username}_{sym}_sma_cross_{int(time.time())}"
        
        order = {
            'user': username,
            'symbol': sym,
            'shares': shares,
            'type': 'conditional_sell',
            'condition': {
                'type': 'sma_cross_below',
                'sma_period': sma_period
            },
            'created_time': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        pending_orders[order_id] = order
        
        console.print(Panel(
            f"🎯 Conditional sell order created!\n"
            f"Symbol: {sym}\n"
            f"Shares: {shares}\n"
            f"Condition: Price crosses below SMA-{sma_period}\n"
            f"Order ID: {order_id}",
            title="📋 Conditional Order Active",
            border_style="blue"
        ))
        return order_id
    
    return None

def place_limit_order(pending_orders, username, sym, shares, target_price, order_type):
    """Place a limit order (buy/sell at specific price)"""
    order_id = f"{username}_{sym}_{order_type}_{int(time.time())}"
    
    order = {
        'user': username,
        'symbol': sym,
        'shares': shares,
        'price': target_price,
        'type': order_type,
        'created_time': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    pending_orders[order_id] = order
    
    console.print(Panel(
        f"📋 Limit order placed successfully!\n"
        f"Order ID: {order_id}\n"
        f"Symbol: {sym}\n"
        f"Shares: {shares}\n"
        f"Target Price: ₹{target_price:.2f}\n"
        f"Order Type: {order_type.upper()}\n"
        f"Status: Pending execution...",
        title="✅ Order Placed",
        border_style="blue"
    ))
    return order_id

def show_help_menu(username=None):
    """Display comprehensive help menu with all available commands"""
    help_table = Table(title="🎯 ULTIMATE STOCK TRADER - COMMAND REFERENCE", style="bold cyan", expand=True)
    help_table.add_column("Category", style="bold blue", width=20)
    help_table.add_column("Command", style="bold green", width=25) 
    help_table.add_column("Description", style="white", width=40)
    
    # Market Data Commands
    help_table.add_row("📊 Market Data", "prices [symbol]", "Live market prices & top movers")
    help_table.add_row("", "top10", "Show top 10 gainers and losers for the day")
    help_table.add_row("", "graph <symbol> [period]", "Technical analysis with SMA overlays") 
    help_table.add_row("", "details <symbol>", "Comprehensive stock information")
    
    # Trading Commands
    help_table.add_row("💱 Trading", "buy <symbol> <shares>", "Market buy order")
    help_table.add_row("", "limitbuy <symbol> <shares> <price>", "Limit buy order")
    help_table.add_row("", "sell <symbol> <shares>", "Market sell order")
    help_table.add_row("", "limitsell <symbol> <shares> <price>", "Limit sell order")
    help_table.add_row("", "sellpct <symbol> <percentage>", "Sell percentage of holdings")
    help_table.add_row("", "sellanalysis <symbol>", "Advanced sell recommendations")
    
    # Risk Management
    help_table.add_row("🛡️ Risk Mgmt", "stoploss <symbol> <shares> <price>", "Set stop-loss protection")
    help_table.add_row("", "trailstop <symbol> <shares> <percent>", "Set trailing stop-loss")
    help_table.add_row("", "orders", "View all active orders")
    help_table.add_row("", "cancel <type> [symbol]", "Cancel orders (stoploss/limit)")
    
    # Portfolio & Tools
    help_table.add_row("📋 Portfolio", "portfolio", "Advanced portfolio analysis")
    help_table.add_row("", "leaderboard", "Top traders ranking")
    help_table.add_row("", "challenge", "Trading competition")
    help_table.add_row("", "refresh", "Update market data")
    help_table.add_row("", "quit", "Exit application")
    
    console.print(Panel(help_table, border_style="cyan", padding=(1, 2)))
    
    # Show admin commands if user is admin
    if username and is_admin(username):
        console.print("\n")
        show_admin_help()
    
    # Quick start tips
    tips = """
💡 [bold]Quick Start Tips:[/bold]
• Type [green]prices[/green] to see current market prices
• Use [green]buy RELIANCE 10[/green] to buy 10 shares of RELIANCE
• Set protection with [yellow]stoploss RELIANCE 10 2500[/yellow]
• View your holdings with [magenta]portfolio[/magenta]
• Check top performers with [cyan]top10[/cyan]
• Get help anytime with [cyan]help[/cyan]
    """
    admin_tip = ""
    if username and is_admin(username):
        admin_tip = "\n🔧 [bold red]Admin Mode Active![/bold red] Use admin commands above for system management."
        
    console.print(Panel(tips + admin_tip, title="🚀 Getting Started", border_style="green"))

def is_admin(username):
    """Check if user has admin privileges"""
    admin_users = ['admin', 'administrator', 'root', 'superuser']
    return username.lower() in admin_users

def show_admin_help():
    """Display admin-specific help menu"""
    admin_table = Table(title="🔧 ADMIN COMMANDS - Privileged Access", style="bold red", expand=True)
    admin_table.add_column("Command", style="bold red", width=30)
    admin_table.add_column("Description", style="white", width=50)
    
    # Admin commands
    admin_table.add_row("listusers", "Display all registered users and their details")
    admin_table.add_row("userinfo <username>", "Get detailed info for specific user")
    admin_table.add_row("resetuser <username>", "Reset user balance and portfolio")
    admin_table.add_row("deleteuser <username>", "Remove user from system")
    admin_table.add_row("setbalance <username> <amount>", "Set user's balance")
    admin_table.add_row("backup", "Create backup of all user data")
    admin_table.add_row("stats", "Show system statistics")
    admin_table.add_row("clearorders", "Clear all pending orders")
    
    console.print(Panel(admin_table, border_style="red", padding=(1, 2)))

def list_all_users(users):
    """Admin function to list all users with their info"""
    if not users:
        console.print(Panel("[yellow]No users registered in the system.[/yellow]", title="👥 User Database", border_style="yellow"))
        return
    
    user_table = Table(title="👥 All Registered Users", style="bold blue", expand=True)
    user_table.add_column("Username", style="bold green", width=15)
    user_table.add_column("Balance", style="cyan", width=15)
    user_table.add_column("Portfolio Value", style="yellow", width=15)
    user_table.add_column("Net Worth", style="bold white", width=15)
    user_table.add_column("Holdings", style="magenta", width=10)
    user_table.add_column("Stop Losses", style="red", width=10)
    
    for username, data in users.items():
        balance = data.get('balance', 0)
        portfolio = data.get('portfolio', {})
        stop_losses = data.get('stop_losses', {})
        
        # Calculate portfolio value (simplified)
        portfolio_value = sum(stock_data.get('shares', 0) * stock_data.get('avg_cost', 0) 
                            for stock_data in portfolio.values())
        net_worth = balance + portfolio_value
        holdings_count = len(portfolio)
        stop_loss_count = len(stop_losses)
        
        user_table.add_row(
            username,
            f"₹{balance:,.2f}",
            f"₹{portfolio_value:,.2f}",
            f"₹{net_worth:,.2f}",
            str(holdings_count),
            str(stop_loss_count)
        )
    
    console.print(Panel(user_table, border_style="blue", padding=(1, 2)))

def get_user_info(users, target_username):
    """Admin function to get detailed info for specific user"""
    if target_username not in users:
        console.print(f"[red]❌ User '{target_username}' not found.[/red]")
        return
    
    user_data = users[target_username]
    balance = user_data.get('balance', 0)
    portfolio = user_data.get('portfolio', {})
    stop_losses = user_data.get('stop_losses', {})
    
    # User info table
    info_table = Table(title=f"👤 User Profile: {target_username}", style="bold green", expand=True)
    info_table.add_column("Attribute", style="bold blue", width=20)
    info_table.add_column("Value", style="white", width=30)
    
    info_table.add_row("💰 Cash Balance", f"₹{balance:,.2f}")
    info_table.add_row("📊 Active Holdings", str(len(portfolio)))
    info_table.add_row("🛡️  Active Stop Losses", str(len(stop_losses)))
    
    console.print(Panel(info_table, border_style="green"))
    
    # Portfolio details
    if portfolio:
        port_table = Table(title="📈 Portfolio Holdings", style="bold cyan", expand=True)
        port_table.add_column("Stock", style="bold white")
        port_table.add_column("Shares", style="green")
        port_table.add_column("Avg Cost", style="yellow")
        port_table.add_column("Total Investment", style="cyan")
        
        for symbol, stock_data in portfolio.items():
            shares = stock_data.get('shares', 0)
            avg_cost = stock_data.get('avg_cost', 0)
            total_investment = shares * avg_cost
            
            port_table.add_row(
                symbol,
                str(shares),
                f"₹{avg_cost:.2f}",
                f"₹{total_investment:,.2f}"
            )
        
        console.print(Panel(port_table, border_style="cyan"))
    
    # Stop losses
    if stop_losses:
        stop_table = Table(title="🛡️  Active Stop Losses", style="bold red", expand=True)
        stop_table.add_column("Stock", style="bold white")
        stop_table.add_column("Shares", style="green")
        stop_table.add_column("Stop Price", style="red")
        stop_table.add_column("Type", style="yellow")
        
        for symbol, stop_data in stop_losses.items():
            shares = stop_data.get('shares', 0)
            stop_price = stop_data.get('price', 0)
            is_trailing = stop_data.get('trailing', False)
            stop_type = "🚂 Trailing" if is_trailing else "🛡️  Fixed"
            
            stop_table.add_row(
                symbol,
                str(shares),
                f"₹{stop_price:.2f}",
                stop_type
            )
        
        console.print(Panel(stop_table, border_style="red"))

def system_stats(users, pending_orders):
    """Show comprehensive system statistics"""
    total_users = len(users)
    total_cash = sum(user.get('balance', 0) for user in users.values())
    total_holdings = sum(len(user.get('portfolio', {})) for user in users.values())
    total_stop_losses = sum(len(user.get('stop_losses', {})) for user in users.values())
    total_pending_orders = len(pending_orders)
    
    stats_table = Table(title="📊 System Statistics", style="bold magenta", expand=True)
    stats_table.add_column("Metric", style="bold blue", width=25)
    stats_table.add_column("Value", style="bold white", width=20)
    
    stats_table.add_row("👥 Total Users", str(total_users))
    stats_table.add_row("💰 Total Cash in System", f"₹{total_cash:,.2f}")
    stats_table.add_row("📈 Total Holdings", str(total_holdings))
    stats_table.add_row("🛡️  Total Stop Losses", str(total_stop_losses))
    stats_table.add_row("📋 Pending Orders", str(total_pending_orders))
    
    console.print(Panel(stats_table, border_style="magenta", padding=(1, 2)))

def show_orders_status(user, pending_orders, username):
    """Show status of all active orders"""
    # Show stop losses
    stop_losses = user.get('stop_losses', {})
    if stop_losses:
        sl_table = Table(title="🛡️  Active Stop Loss Orders", style="bold red")
        sl_table.add_column("Symbol", style="cyan")
        sl_table.add_column("Shares", justify="right", style="yellow")
        sl_table.add_column("Stop Price", justify="right", style="red")
        sl_table.add_column("Set Time", style="white")
        
        for sym, data in stop_losses.items():
            set_time = datetime.fromisoformat(data['set_time']).strftime("%m/%d %H:%M")
            sl_table.add_row(sym, str(data['shares']), f"₹{data['price']:.2f}", set_time)
        
        console.print(Panel(sl_table, border_style="red"))
    
    # Show limit orders
    user_limit_orders = {k: v for k, v in pending_orders.items() if v['user'] == username}
    if user_limit_orders:
        lo_table = Table(title="📋 Active Limit Orders", style="bold blue")
        lo_table.add_column("Order ID", style="cyan", width=20)
        lo_table.add_column("Type", style="white")
        lo_table.add_column("Symbol", style="yellow")
        lo_table.add_column("Shares", justify="right")
        lo_table.add_column("Target Price", justify="right", style="green")
        lo_table.add_column("Status", style="blue")
        
        for order_id, order in user_limit_orders.items():
            order_type = "🔵 BUY" if order['type'] == 'buy' else "🔴 SELL"
            lo_table.add_row(
                order_id[-10:],  # Show last 10 chars
                order_type,
                order['symbol'],
                str(order['shares']),
                f"₹{order['price']:.2f}",
                "⏳ Pending"
            )
        
        console.print(Panel(lo_table, border_style="blue"))
    
    if not stop_losses and not user_limit_orders:
        console.print(Panel("No active orders", title="📋 Orders Status", style="yellow"))

def cancel_order(user, pending_orders, username, order_type, symbol=None):
    """Cancel orders (stop loss or limit orders)"""
    if order_type == "stoploss":
        stop_losses = user.get('stop_losses', {})
        if symbol and symbol in stop_losses:
            del stop_losses[symbol]
            console.print(f"[green]✅ Stop loss for {symbol} cancelled.[/green]")
        elif not symbol:
            stop_losses.clear()
            console.print("[green]✅ All stop loss orders cancelled.[/green]")
        else:
            console.print(f"[red]❌ No stop loss found for {symbol}.[/red]")
    
    elif order_type == "limit":
        user_orders = [k for k, v in pending_orders.items() if v['user'] == username]
        if symbol:
            cancelled = []
            for order_id in list(user_orders):
                if pending_orders[order_id]['symbol'] == symbol:
                    del pending_orders[order_id]
                    cancelled.append(order_id)
            if cancelled:
                console.print(f"[green]✅ {len(cancelled)} limit order(s) for {symbol} cancelled.[/green]")
            else:
                console.print(f"[red]❌ No limit orders found for {symbol}.[/red]")
        else:
            for order_id in user_orders:
                del pending_orders[order_id]
            console.print(f"[green]✅ {len(user_orders)} limit order(s) cancelled.[/green]")

def show_enhanced_portfolio(user, stocks):
    """Enhanced portfolio display with advanced metrics"""
    enhanced_loading_animation("Analyzing portfolio...")
    
    portfolio_table = Table(title="💼 Your Investment Portfolio", style="bold magenta", expand=True)
    portfolio_table.add_column("Stock", style="cyan", width=8)
    portfolio_table.add_column("Shares", justify="right", style="yellow", width=8)
    portfolio_table.add_column("Avg Cost", justify="right", style="white", width=10)
    portfolio_table.add_column("Current Price", justify="right", style="white", width=12)
    portfolio_table.add_column("Market Value", justify="right", style="green", width=12)
    portfolio_table.add_column("P/L ₹", justify="right", width=10)
    portfolio_table.add_column("P/L %", justify="right", width=8)
    portfolio_table.add_column("Allocation", justify="center", width=10)
    
    total_value = 0
    total_pl = 0
    total_invested = 0
    
    for sym, data in user['portfolio'].items():
        shares = data.get('shares', 0)
        avg_cost = data.get('avg_cost', 0.0)
        invested_amount = shares * avg_cost
        
        stock = next((s for s in stocks if s['symbol'] == sym), None)
        if not stock:
            stock = fetch_single_price(sym)
        current_price = stock['price'] if stock and isinstance(stock, dict) else avg_cost
        
        market_value = shares * current_price
        pl_amount = market_value - invested_amount
        pl_percentage = (pl_amount / invested_amount * 100) if invested_amount > 0 else 0
        
        # Calculate allocation percentage (will be updated after total is known)
        total_value += market_value
        total_pl += pl_amount
        total_invested += invested_amount
    
    # Now add rows with allocation percentages
    for sym, data in user['portfolio'].items():
        shares = data.get('shares', 0)
        avg_cost = data.get('avg_cost', 0.0)
        invested_amount = shares * avg_cost
        
        stock = next((s for s in stocks if s['symbol'] == sym), None)
        if not stock:
            stock = fetch_single_price(sym)
        current_price = stock['price'] if stock and isinstance(stock, dict) else avg_cost
        
        market_value = shares * current_price
        pl_amount = market_value - invested_amount
        pl_percentage = (pl_amount / invested_amount * 100) if invested_amount > 0 else 0
        allocation = (market_value / total_value * 100) if total_value > 0 else 0
        
        # Color coding for P/L
        pl_color = "bright_green" if pl_amount > 0 else "bright_red" if pl_amount < 0 else "white"
        pl_amount_str = f"[{pl_color}]{pl_amount:+,.2f}[/{pl_color}]"
        pl_percentage_str = f"[{pl_color}]{pl_percentage:+.1f}%[/{pl_color}]"
        
        # Progress bar for allocation
        allocation_bar = "█" * int(allocation / 10) + "░" * (10 - int(allocation / 10))
        allocation_str = f"{allocation:.1f}%"
        
        portfolio_table.add_row(
            sym, 
            str(shares), 
            f"₹{avg_cost:.2f}",
            f"₹{current_price:.2f}", 
            f"₹{market_value:,.2f}",
            pl_amount_str,
            pl_percentage_str,
            allocation_str
        )
    
    net_worth = user['balance'] + total_value
    overall_return = (total_pl / total_invested * 100) if total_invested > 0 else 0
    
    console.print(Panel(portfolio_table, title="📊 Portfolio Analysis", border_style="bright_blue"))
    
    # Portfolio summary with enhanced metrics
    summary_table = Table.grid(padding=2)
    summary_table.add_column(style="bold cyan", justify="right")
    summary_table.add_column(style="bold white")
    summary_table.add_column(style="bold cyan", justify="right")
    summary_table.add_column(style="bold white")
    
    pl_color = "bright_green" if total_pl > 0 else "bright_red" if total_pl < 0 else "white"
    return_color = "bright_green" if overall_return > 0 else "bright_red" if overall_return < 0 else "white"
    
    summary_table.add_row("💰 Cash Balance:", f"₹{user['balance']:,.2f}", "📊 Portfolio Value:", f"₹{total_value:,.2f}")
    summary_table.add_row("💎 Net Worth:", f"₹{net_worth:,.2f}", "💰 Total Invested:", f"₹{total_invested:,.2f}")
    summary_table.add_row("📈 Total P/L:", f"[{pl_color}]₹{total_pl:+,.2f}[/{pl_color}]", "📊 Overall Return:", f"[{return_color}]{overall_return:+.1f}%[/{return_color}]")
    summary_table.add_row("📋 Holdings:", f"{len(user['portfolio'])} stocks", "🛡️  Stop Losses:", f"{len(user.get('stop_losses', {}))} active")
    
    console.print(Panel(summary_table, title="💼 Portfolio Summary", border_style="green"))

def main():
    console.clear()
    console.print(Panel(ASCII_LOGO, title="🚀 Ultimate Stock Trader Pro", style="bold cyan", padding=(1, 2)))
    
    # Load data
    users = load_data(USERS_FILE, {})
    leaderboard = load_data(LEADERBOARD_FILE, {})
    pending_orders = load_data(ORDERS_FILE, {})
    stocks = []
    tracked_symbols = SYMBOLS.copy()
    
    # User authentication
    console.print("\n🎯 [bold]Enter your trading credentials:[/bold]")
    username = console.input("👤 Username: ").strip()
    
    
    if not username:
        console.print("❌ [red]Username cannot be empty.[/red]")
        return
    
    if username not in users:
        users[username] = {'balance': 10000.0, 'portfolio': {}, 'stop_losses': {}}
        console.print("🎉 [green]Welcome! New trader account created with ₹10,000 starting capital![/green]")
    
    user = users[username]
    console.print(f"👋 [bold]Welcome back, {username}![/bold]")
    
    # Load market data
    enhanced_loading_animation("Connecting to live markets...", 1.5)
    stocks = fetch_prices()
    if not stocks:
        console.print("⚠️  [yellow]Live market data unavailable. Some features may be limited.[/yellow]")
    
    # Show initial status
    console.print(Rule(f"🎯 ULTIMATE TRADER - {username}", style="bold green"))
    console.print(create_status_panel(user, stocks))
    console.print("\n💡 [dim]Type [bold cyan]help[/bold cyan] to see all available commands[/dim]")
    
    while True:
        # Check and execute stop losses
        executed_stop_losses = check_stop_losses(user, stocks)
    
        # Process limit orders
        executed_limit_orders = process_limit_orders(pending_orders, stocks, users)
    
        cmd = console.input("\n🎯 [bold]ultimate-trader>[/bold] ").strip().lower()
        parts = cmd.split()
    
        if not parts:
            continue
    
        # Flag to track if we should show status after command
        show_status = False
    
        # Help Command
        if parts[0] == 'help':
            show_help_menu(username)
            show_status = True
    
        # Market Data Commands
        elif parts[0] == 'prices':
            if len(parts) == 2:
                show_enhanced_prices(stocks, parts[1].upper())
            else:
                show_enhanced_prices(stocks)
    
        elif parts[0] == 'top10':
            show_top10(stocks)
    
        elif parts[0] == 'details':
            if len(parts) != 2:
                console.print(Panel(
                    f"❌ Incomplete command: 'details' requires a stock symbol\n"
                    f"💡 Usage: details <symbol> (e.g., details RELIANCE)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue

            # Using the original show_stock_details function
            try:
                ticker = yf.Ticker(f"{parts[1].upper()}.NS")
                info = ticker.info
                hist = ticker.history(period="1y")

                if not info or hist.empty:
                    console.print(f"[red]No data available for {parts[1].upper()}.[/red]")
                    continue

                table = Table(title=f"Stock Details for {parts[1].upper()}", style="bold magenta", expand=True)
                table.add_column("Attribute", style="cyan")
                table.add_column("Value", style="green")

                # Basic price data
                table.add_row("Current Price", f"₹{info.get('currentPrice', 'N/A'):.2f}")
                table.add_row("Open", f"₹{info.get('open', 'N/A'):.2f}")
                table.add_row("Previous Close", f"₹{info.get('previousClose', 'N/A'):.2f}")

                # 52-week range
                if not hist.empty:
                    high_52w = hist['High'].max()
                    low_52w = hist['Low'].min()
                    table.add_row("52-Week High", f"₹{high_52w:.2f}")
                    table.add_row("52-Week Low", f"₹{low_52w:.2f}")
                else:
                    table.add_row("52-Week High", "N/A")
                    table.add_row("52-Week Low", "N/A")

                # Volume and market data
                table.add_row("Volume", f"{info.get('volume', 'N/A'):,}" if info.get('volume') else "N/A")
                table.add_row("Average Volume", f"{info.get('averageVolume', 'N/A'):,}" if info.get('averageVolume') else "N/A")
                table.add_row("Market Cap", f"₹{info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else "N/A")
                table.add_row("P/E Ratio", f"{info.get('trailingPE', 'N/A'):.2f}" if info.get('trailingPE') else "N/A")
                table.add_row("Dividend Yield", f"{info.get('dividendYield', 'N/A')*100:.2f}%" if info.get('dividendYield') else "N/A")

                console.print(Panel(table, title="Stock Overview", border_style="bright_blue"))

            except Exception as e:
                console.print(f"[red]Error fetching details for {parts[1].upper()}: {e}[/red]")
        
        elif parts[0] == 'graph':
            if len(parts) < 2:
                console.print(Panel(
                    f"❌ Incomplete command: 'graph' requires a stock symbol\n"
                    f"💡 Usage: graph <symbol> [period] (e.g., graph RELIANCE 3mo)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            period = parts[2] if len(parts) > 2 else "3mo"
            show_ultimate_graph(parts[1].upper(), period)
        
        # Trading Commands
        elif parts[0] == 'buy':
            if len(parts) != 3:
                console.print(Panel(
                    f"❌ Incomplete command: 'buy' requires stock symbol and number of shares\n"
                    f"💡 Usage: buy <symbol> <shares> (e.g., buy RELIANCE 10)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            # Traditional market buy (existing functionality)
            stock = next((s for s in stocks if s['symbol'] == parts[1].upper()), None)
            if not stock:
                stock = fetch_single_price(parts[1].upper())
                if stock:
                    stocks.append(stock)
                    if f"{parts[1].upper()}.NS" not in tracked_symbols:
                        tracked_symbols.append(f"{parts[1].upper()}.NS")
                else:
                    console.print("[red]Stock data unavailable.[/red]")
                    continue
            try:
                shares = int(parts[2])
                if shares <= 0:
                    raise ValueError
            except ValueError:
                console.print("[red]Invalid number of shares.[/red]")
                continue
            current_price = stock['price']
            cost = current_price * shares
            if user['balance'] < cost:
                console.print("[red]Insufficient balance.[/red]")
                continue
            console.print(Panel(f"[yellow]Current price for {parts[1].upper()}: ₹{current_price:.2f}[/yellow]", border_style="yellow"))
            cmd_confirm = console.input(f"[bold]Confirm buy {shares} of {parts[1].upper()} at ₹{current_price:.2f} each? (yes/no): [/bold]").strip().lower()
            if cmd_confirm != 'yes':
                console.print("[yellow]Transaction cancelled.[/yellow]")
                continue
            user['balance'] -= cost
            sym = parts[1].upper()
            if sym not in user['portfolio']:
                user['portfolio'][sym] = {'shares': shares, 'avg_cost': current_price}
            else:
                old_data = user['portfolio'][sym]
                old_shares = old_data['shares']
                old_avg = old_data['avg_cost']
                new_shares = old_shares + shares
                new_avg = (old_avg * old_shares + current_price * shares) / new_shares
                user['portfolio'][sym] = {'shares': new_shares, 'avg_cost': new_avg}
            console.print(Panel(f"[green]✅ Bought {shares} shares of {sym} for ₹{cost:.2f}.[/green]", border_style="green"))
        
        elif parts[0] == 'limitbuy':
            if len(parts) != 4:
                console.print(Panel(
                    f"❌ Incomplete command: 'limitbuy' requires stock symbol, shares, and target price\n"
                    f"💡 Usage: limitbuy <symbol> <shares> <price> (e.g., limitbuy RELIANCE 10 2500)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            try:
                shares = int(parts[2])
                target_price = float(parts[3])
                if shares <= 0 or target_price <= 0:
                    raise ValueError
                
                # Check if user has enough balance
                estimated_cost = target_price * shares
                if user['balance'] < estimated_cost:
                    console.print(f"[red]❌ Insufficient balance. Need ₹{estimated_cost:.2f} but have ₹{user['balance']:.2f}[/red]")
                    continue
                
                order_id = place_limit_order(pending_orders, username, parts[1].upper(), shares, target_price, 'buy')
                
            except ValueError:
                console.print("[red]❌ Invalid shares or price.[/red]")
        
        elif parts[0] == 'sell':
            if len(parts) != 3:
                console.print(Panel(
                    f"❌ Incomplete command: 'sell' requires stock symbol and number of shares\n"
                    f"💡 Usage: sell <symbol> <shares> (e.g., sell RELIANCE 10)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            sym = parts[1].upper()
            if sym not in user['portfolio']:
                console.print("[red]❌ You don't own this stock.[/red]")
                continue
            stock = next((s for s in stocks if s['symbol'] == sym), None)
            if not stock:
                stock = fetch_single_price(sym)
                if not stock:
                    continue
            try:
                shares = int(parts[2])
                if shares <= 0 or shares > user['portfolio'][sym]['shares']:
                    raise ValueError
            except ValueError:
                console.print("[red]❌ Invalid number of shares.[/red]")
                continue
            current_price = stock['price']
            revenue = current_price * shares
            console.print(Panel(f"[yellow]Current price for {sym}: ₹{current_price:.2f}[/yellow]", border_style="yellow"))
            cmd_confirm = console.input(f"[bold]Confirm sell {shares} of {sym} at ₹{current_price:.2f} each? (yes/no): [/bold]").strip().lower()
            if cmd_confirm != 'yes':
                console.print("[yellow]Transaction cancelled.[/yellow]")
                continue
            user['balance'] += revenue
            user['portfolio'][sym]['shares'] -= shares
            if user['portfolio'][sym]['shares'] == 0:
                del user['portfolio'][sym]
            console.print(Panel(f"[green]✅ Sold {shares} shares of {sym} for ₹{revenue:.2f}.[/green]", border_style="green"))
        
        elif parts[0] == 'limitsell':
            if len(parts) != 4:
                console.print(Panel(
                    f"❌ Incomplete command: 'limitsell' requires stock symbol, shares, and target price\n"
                    f"💡 Usage: limitsell <symbol> <shares> <price> (e.g., limitsell RELIANCE 10 2600)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            try:
                sym = parts[1].upper()
                shares = int(parts[2])
                target_price = float(parts[3])
                
                if shares <= 0 or target_price <= 0:
                    raise ValueError
                
                # Check if user owns enough shares
                if sym not in user['portfolio'] or user['portfolio'][sym]['shares'] < shares:
                    available = user['portfolio'].get(sym, {}).get('shares', 0)
                    console.print(f"[red]❌ Insufficient shares. You have {available} shares of {sym}[/red]")
                    continue
                
                order_id = place_limit_order(pending_orders, username, sym, shares, target_price, 'sell')
                
            except ValueError:
                console.print("[red]❌ Invalid shares or price.[/red]")
        
        elif parts[0] == 'sellpct':
            if len(parts) != 3:
                console.print(Panel(
                    f"❌ Incomplete command: 'sellpct' requires stock symbol and percentage\n"
                    f"💡 Usage: sellpct <symbol> <percentage> (e.g., sellpct RELIANCE 50)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            try:
                sym = parts[1].upper()
                percentage = float(parts[2])
                
                sell_percentage(user, sym, percentage, stocks)
                
            except ValueError:
                console.print("[red]❌ Invalid percentage.[/red]")
        
        elif parts[0] == 'sellanalysis':
            if len(parts) != 2:
                console.print(Panel(
                    f"❌ Incomplete command: 'sellanalysis' requires a stock symbol\n"
                    f"💡 Usage: sellanalysis <symbol> (e.g., sellanalysis RELIANCE)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            sym = parts[1].upper()
            analysis = advanced_sell_analysis(user, sym, stocks)
            
            if analysis:
                # Display comprehensive sell analysis
                analysis_table = Table(title=f"🎯 Advanced Sell Analysis for {sym}", style="bold cyan")
                analysis_table.add_column("Metric", style="white", width=20)
                analysis_table.add_column("Value", style="green", width=15)
                analysis_table.add_column("Assessment", style="yellow", width=25)
                
                profit_color = "bright_green" if analysis['profit_loss_pct'] > 0 else "bright_red"
                analysis_table.add_row("💰 Current Price", f"₹{analysis['current_price']:.2f}", "Live market price")
                analysis_table.add_row("💵 Your Avg Cost", f"₹{analysis['avg_cost']:.2f}", "Your purchase average")
                analysis_table.add_row("📊 P/L %", f"[{profit_color}]{analysis['profit_loss_pct']:+.1f}%[/{profit_color}]", "Your profit/loss")
                analysis_table.add_row("📈 SMA 20", f"₹{analysis['sma_20']:.2f}", "20-day moving average")
                analysis_table.add_row("📊 SMA 50", f"₹{analysis['sma_50']:.2f}", "50-day moving average")
                
                console.print(Panel(analysis_table, border_style="cyan"))
                
                if analysis['recommendations']:
                    rec_panel = "\n".join([f"• {rec}" for rec in analysis['recommendations']])
                    console.print(Panel(rec_panel, title="💡 Selling Recommendations", border_style="yellow"))
                else:
                    console.print(Panel("📊 No specific recommendations at this time. Monitor market conditions.", 
                                        title="💡 Analysis", border_style="blue"))
            else:
                console.print("[red]❌ Unable to analyze this stock. Make sure you own it and data is available.[/red]")
        
        # Risk Management Commands
        elif parts[0] == 'stoploss':
            if len(parts) != 4:
                console.print(Panel(
                    f"❌ Incomplete command: 'stoploss' requires stock symbol, shares, and stop price\n"
                    f"💡 Usage: stoploss <symbol> <shares> <price> (e.g., stoploss RELIANCE 10 2400)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            try:
                sym = parts[1].upper()
                shares = int(parts[2])
                stop_price = float(parts[3])
                
                if shares <= 0 or stop_price <= 0:
                    raise ValueError
                    
                set_stop_loss(user, sym, shares, stop_price)
                
            except ValueError:
                console.print("[red]❌ Invalid shares or price.[/red]")
        
        elif parts[0] == 'trailstop':
            if len(parts) != 4:
                console.print(Panel(
                    f"❌ Incomplete command: 'trailstop' requires stock symbol, shares, and trailing percentage\n"
                    f"💡 Usage: trailstop <symbol> <shares> <percent> (e.g., trailstop RELIANCE 10 5)",
                    title="⚠️ Command Help", border_style="yellow"))
                continue
            try:
                sym = parts[1].upper()
                shares = int(parts[2])
                trailing_percent = float(parts[3])
                
                if shares <= 0 or trailing_percent <= 0 or trailing_percent >= 100:
                    raise ValueError
                    
                set_stop_loss(user, sym, shares, 0, trailing=True, trailing_percent=trailing_percent)
                
            except ValueError:
                console.print("[red]❌ Invalid shares or percentage (must be 0-100).[/red]")
        
        elif parts[0] == 'orders':
            show_orders_status(user, pending_orders, username)
        
        elif parts[0] == 'cancel' and len(parts) >= 2:
            order_type = parts[1]
            symbol = parts[2].upper() if len(parts) > 2 else None
            cancel_order(user, pending_orders, username, order_type, symbol)
        
        # Portfolio & Analysis
        elif parts[0] == 'portfolio':
            show_enhanced_portfolio(user, stocks)
        
        elif parts[0] == 'leaderboard':
            current_net_worth = calculate_net_worth(user, stocks)
            leaderboard[username] = current_net_worth
            
            table = Table(title="🏆 Top Traders Leaderboard", style="bold magenta", expand=True)
            table.add_column("Rank", style="yellow", width=6)
            table.add_column("Trader", style="cyan", width=15)
            table.add_column("Net Worth", justify="right", style="green", width=15)
            table.add_column("Status", justify="center", width=10)
            
            sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
            for rank, (trader, score) in enumerate(sorted_lb, 1):
                status = "👑" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "⭐"
                if trader == username:
                    trader = f"[bold]{trader} (You)[/bold]"
                table.add_row(str(rank), trader, f"₹{score:,.2f}", status)
            
            console.print(Panel(table, title="🏆 Elite Traders", border_style="bright_blue"))
        
        # Utility Commands
        elif parts[0] == 'refresh':
            enhanced_loading_animation("Refreshing market data...", 1.0)
            new_stocks = fetch_prices()
            if new_stocks:
                stocks = new_stocks
                console.print("[green]✅ Market data refreshed![/green]")
            else:
                console.print("[yellow]⚠️  Failed to refresh market data.[/yellow]")
        
        # Admin Commands (only for admin users)
        elif is_admin(username):
            if parts[0] == 'listusers':
                list_all_users(users)
            
            elif parts[0] == 'userinfo':
                if len(parts) != 2:
                    console.print(Panel(
                        f"❌ Incomplete command: 'userinfo' requires a username\n"
                        f"💡 Usage: userinfo <username> (e.g., userinfo john)",
                        title="⚠️ Command Help", border_style="yellow"))
                    continue
                get_user_info(users, parts[1])
            
            elif parts[0] == 'resetuser':
                if len(parts) != 2:
                    console.print(Panel(
                        f"❌ Incomplete command: 'resetuser' requires a username\n"
                        f"💡 Usage: resetuser <username> (e.g., resetuser john)",
                        title="⚠️ Command Help", border_style="yellow"))
                    continue
                target_user = parts[1]
                if target_user in users:
                    confirm = console.input(f"[bold red]⚠️  Reset user '{target_user}' to default state? (yes/no): [/bold red]").strip().lower()
                    if confirm == 'yes':
                        users[target_user] = {'balance': 10000.0, 'portfolio': {}, 'stop_losses': {}}
                        console.print(Panel(f"✅ User '{target_user}' has been reset to default state.", 
                                          title="🔄 User Reset", border_style="green"))
                    else:
                        console.print("[yellow]Reset cancelled.[/yellow]")
                else:
                    console.print(f"[red]❌ User '{target_user}' not found.[/red]")
            
            elif parts[0] == 'deleteuser':
                if len(parts) != 2:
                    console.print(Panel(
                        f"❌ Incomplete command: 'deleteuser' requires a username\n"
                        f"💡 Usage: deleteuser <username> (e.g., deleteuser john)",
                        title="⚠️ Command Help", border_style="yellow"))
                    continue
                target_user = parts[1]
                if target_user in users:
                    if target_user == username:
                        console.print("[red]❌ You cannot delete yourself![/red]")
                    else:
                        confirm = console.input(f"[bold red]⚠️  PERMANENTLY DELETE user '{target_user}'? (yes/no): [/bold red]").strip().lower()
                        if confirm == 'yes':
                            del users[target_user]
                            # Also remove from leaderboard
                            if target_user in leaderboard:
                                del leaderboard[target_user]
                            console.print(Panel(f"🗑️  User '{target_user}' has been permanently deleted.", 
                                              title="❌ User Deleted", border_style="red"))
                        else:
                            console.print("[yellow]Delete cancelled.[/yellow]")
                else:
                    console.print(f"[red]❌ User '{target_user}' not found.[/red]")
            
            elif parts[0] == 'setbalance':
                if len(parts) != 3:
                    console.print(Panel(
                        f"❌ Incomplete command: 'setbalance' requires username and amount\n"
                        f"💡 Usage: setbalance <username> <amount> (e.g., setbalance john 15000)",
                        title="⚠️ Command Help", border_style="yellow"))
                    continue
                target_user = parts[1]
                try:
                    new_balance = float(parts[2])
                    if target_user in users:
                        old_balance = users[target_user].get('balance', 0)
                        users[target_user]['balance'] = new_balance
                        console.print(Panel(
                            f"💰 Balance updated for '{target_user}'\n"
                            f"Old Balance: ₹{old_balance:,.2f}\n"
                            f"New Balance: ₹{new_balance:,.2f}",
                            title="💳 Balance Update", border_style="green"))
                    else:
                        console.print(f"[red]❌ User '{target_user}' not found.[/red]")
                except ValueError:
                    console.print("[red]❌ Invalid balance amount.[/red]")
            
            elif parts[0] == 'backup':
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"backup_users_{timestamp}.json"
                try:
                    with open(backup_file, 'w') as f:
                        json.dump(users, f, indent=2)
                    console.print(Panel(f"✅ User data backed up to: {backup_file}", 
                                      title="💾 Backup Created", border_style="green"))
                except Exception as e:
                    console.print(f"[red]❌ Backup failed: {e}[/red]")
            
            elif parts[0] == 'stats':
                system_stats(users, pending_orders)
            
            elif parts[0] == 'clearorders':
                order_count = len(pending_orders)
                if order_count > 0:
                    confirm = console.input(f"[bold red]⚠️  Clear {order_count} pending orders? (yes/no): [/bold red]").strip().lower()
                    if confirm == 'yes':
                        pending_orders.clear()
                        console.print(Panel(f"🧹 Cleared {order_count} pending orders.", 
                                          title="📋 Orders Cleared", border_style="yellow"))
                    else:
                        console.print("[yellow]Clear cancelled.[/yellow]")
                else:
                    console.print("[yellow]No pending orders to clear.[/yellow]")
            
            elif parts[0] == 'quit':
                console.print("[bold]💾 Saving admin session...[/bold]")
                enhanced_loading_animation("Saving data...", 0.5)
                break
            
        elif parts[0] == 'quit':
            console.print("[bold]💾 Saving trading session...[/bold]")
            enhanced_loading_animation("Saving data...", 0.5)
            break
        
        else:
            # Check if it's a partial match for known commands
            known_commands = ['help', 'prices', 'details', 'graph', 'buy', 'limitbuy', 'sell', 'limitsell', 'sellpct', 'sellanalysis', 'stoploss', 'trailstop', 'orders', 'cancel', 'portfolio', 'leaderboard', 'challenge', 'refresh', 'quit']
            if is_admin(username):
                known_commands.extend(['listusers', 'userinfo', 'resetuser', 'deleteuser', 'setbalance', 'backup', 'stats', 'clearorders'])
            
            # Check for partial matches
            partial_matches = [cmd for cmd in known_commands if cmd.startswith(parts[0])]
            
            if partial_matches:
                suggestions = ', '.join(partial_matches)
                console.print(Panel(
                    f"❓ Did you mean: {suggestions}?\n"
                    f"💡 Type [cyan]help[/cyan] to see all available commands.",
                    title="🤔 Possible Command", border_style="yellow"))
            else:
                console.print(Panel(
                    f"❌ Unknown command: '{parts[0]}'\n"
                    f"💡 Type [cyan]help[/cyan] to see all available commands.",
                    title="⚠️  Command Error", border_style="red"))
        
        # Show status panel after certain commands
        if show_status:
            console.print("\n" + "─" * 80)
            console.print(create_status_panel(user, stocks))
        
        # Save data after each transaction
        save_data(USERS_FILE, users)
        save_data(LEADERBOARD_FILE, leaderboard) 
        save_data(ORDERS_FILE, pending_orders)
    
    console.print(Panel(
        "🎉 Thank you for using Ultimate Stock Trader!\n"
        "💎 Your trading journey continues...\n"
        "📈 Happy investing and may the markets be with you! 🚀",
        title="👋 Farewell, Elite Trader",
        style="bold green"
    ))

if __name__ == "__main__":
    main()
