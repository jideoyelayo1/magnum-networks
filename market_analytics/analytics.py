import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import CheckButtons
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

PLAYER_MAP = {
    "SGIL": "Shai Gilgeous-Alexander",
    "NJOK": "Nikola Jokic",
    "LDON": "Luka Doncic",
    "AEDW": "Anthony Edwards",
}

class MultiMarketDashboard:
    def __init__(self, db_path, poll_interval=2000):
        self.db_path = db_path
        self.poll_interval = poll_interval
        
        # UI State Toggles
        self.show_ma = False
        self.show_monte_carlo = False
        
        self.fig = plt.figure(figsize=(14, 10))
        self.fig.suptitle('Live Arbitrage Dashboard with Projections', fontsize=16)
        plt.style.use('bmh')
        
        self.fig.subplots_adjust(bottom=0.15)
        self.rax = self.fig.add_axes([0.4, 0.02, 0.2, 0.08])
        self.check = CheckButtons(self.rax, ['Moving Average', 'Monte Carlo'], [False, False])
        self.check.on_clicked(self.toggle_widgets)
        
        self.ani = None

    def toggle_widgets(self, label):
        if label == 'Moving Average':
            self.show_ma = not self.show_ma
        elif label == 'Monte Carlo':
            self.show_monte_carlo = not self.show_monte_carlo

    def fetch_data(self):
        query = "SELECT * FROM market_snapshots ORDER BY timestamp ASC"
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn)
            if df.empty: return pd.DataFrame()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logging.error(f"SQL Error: {e}")
            return pd.DataFrame()

    def run_monte_carlo(self, data, steps=10, sims=20):
        """Simulates potential future prices based on historical volatility."""
        if len(data) < 2: return None
        prices = data['price'].values
        returns = np.diff(np.log(prices + 1e-6))
        mu = np.mean(returns)
        sigma = np.std(returns) if np.std(returns) > 0 else 0.01
        
        last_price = prices[-1]
        last_time = data['timestamp'].iloc[-1]
        
        # Project future timestamps
        future_times = [last_time + pd.Timedelta(minutes=5*i) for i in range(steps + 1)]
        
        paths = np.zeros((steps + 1, sims))
        paths[0] = last_price
        for t in range(1, steps + 1):
            rand_walk = np.random.normal(mu, sigma, sims)
            paths[t] = paths[t-1] * np.exp(rand_walk)
            
        return future_times, paths

    def determine_source_and_player(self, row):
        row_str = str(row.values).lower()
        player_name = "Unknown"
        for ticker, name in PLAYER_MAP.items():
            if ticker.lower() in row_str or name.lower() in row_str:
                player_name = name
                break
        source = "Polymarket"
        if 'source' in row and 'kalshi' in str(row['source']).lower():
            source = 'Kalshi'
        elif any(t.lower() in str(row.get('market_id','')).lower() for t in PLAYER_MAP.keys()):
            source = "Kalshi"
        return pd.Series([player_name, source], index=['player_name', 'platform_source'])

    def update_plot(self, frame):
        df_raw = self.fetch_data()
        if df_raw.empty: return

        meta = df_raw.apply(self.determine_source_and_player, axis=1)
        df = pd.concat([df_raw, meta], axis=1)
        df = df[df['player_name'] != "Unknown"]
        
        groups = df.groupby('player_name')
        num_groups = len(groups)
        if num_groups == 0: return

        for ax in self.fig.axes:
            if ax != self.rax:
                ax.remove()
        
        cols = 2
        rows = (num_groups + 1) // cols
        
        for i, (player, data) in enumerate(groups):
            if i >= 6: break
            ax = self.fig.add_subplot(rows, cols, i + 1)
            
            for src, color, style in [('Kalshi', '#00d1b2', '-'), ('Polymarket', '#3273dc', '--')]:
                src_data = data[data['platform_source'] == src]
                if not src_data.empty:
                    ax.plot(src_data['timestamp'], src_data['price'], label=src, color=color, linestyle=style, alpha=0.8)
                    
                    # 1. MOVING AVERAGE
                    if self.show_ma:
                        ma = src_data['price'].rolling(window=50).mean()
                        ax.plot(src_data['timestamp'], ma, color='orange', linewidth=1, label=f'{src} SMA')
                    
                    # 2. MONTE CARLO
                    if self.show_monte_carlo and src == 'Kalshi':
                        mc_res = self.run_monte_carlo(src_data, sims = 50)
                        if mc_res:
                            f_times, f_paths = mc_res
                            ax.plot(f_times, f_paths, color='gray', alpha=0.1, linewidth=0.5)
            
            ax.set_title(player, fontsize=10)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.set_ylim(0, 1)
            if i == 0: ax.legend(loc='upper left', fontsize='x-small')

        self.fig.canvas.draw_idle()

    def run(self):
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=self.poll_interval, cache_frame_data=False)
        plt.show()

if __name__ == "__main__":
    dashboard = MultiMarketDashboard("markets.db")
    dashboard.run()