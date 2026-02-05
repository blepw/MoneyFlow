from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import matplotlib.pyplot as plt
import networkx as nx
from datetime import datetime
import threading
from collections import defaultdict
import pyperclip
import re
from enum import Enum
from matplotlib.patches import Patch
import time


class Cryptocurrency(Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    XRP = "ripple"
    SOLANA = "solana"
    

CRYPTO_CONFIGS = {
    Cryptocurrency.BITCOIN: {
        "name": "Bitcoin",
        "symbol": "BTC",
        "explorer": "blockchain.info",
        "api_base": "https://blockchain.info",
        "decimals": 8,
        "color": "#F7931A", 
    },
    Cryptocurrency.ETHEREUM: {
        "name": "Ethereum",
        "symbol": "ETH",
        "explorer": "etherscan.io",
        "api_base": "https://api.etherscan.io/api",
        "decimals": 18,
        "color": "#627EEA",  
    },
    Cryptocurrency.XRP: {
        "name": "XRP",
        "symbol": "XRP",
        "explorer": "xrpscan.com",
        "api_base": "https://api.xrpscan.com/api/v1",
        "decimals": 6,
        "color": "#FF0000", 
    },
    Cryptocurrency.SOLANA: {
        "name": "Solana",
        "symbol": "SOL",
        "explorer": "solscan.io",
        "api_base": "https://public-api.solscan.io",
        "decimals": 9,
        "color": "#00FFA3",
    }
}

class MultiCryptoAPI:    
    def __init__(self, error_callback=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.error_callback = error_callback
    
    def show_error(self, message):
        """Display error message through callback"""
        if self.error_callback:
            self.error_callback(message)
    
    def validate_address(self, crypto, address):
        if crypto == Cryptocurrency.BITCOIN:
            return self.validate_bitcoin_address(address)
        elif crypto == Cryptocurrency.ETHEREUM:
            return self.validate_ethereum_address(address)
        elif crypto == Cryptocurrency.XRP:
            return self.validate_xrp_address(address)
        elif crypto == Cryptocurrency.SOLANA:
            return self.validate_solana_address(address)
        return False

    
    def validate_bitcoin_address(self, address):
        """Validate Bitcoin address (supports P2PKH, P2SH, and Bech32)"""
        address = address.strip()
        
        # P2PKH(1)
        if re.match(r'^1[1-9A-HJ-NP-Za-km-z]{25,34}$', address):
            return True
        
        # P2SH (3)
        if re.match(r'^3[1-9A-HJ-NP-Za-km-z]{25,34}$', address):
            return True
        
        # Bech32 (bc1)
        if address.startswith('bc1'):
            if len(address) < 42 or len(address) > 62:
                return False
            if not re.match(r'^bc1[02-9ac-hj-np-z]{11,71}$', address.lower()):
                return False
            return True
        
        # Testnet
        if address.startswith('tb1') or address.startswith('2') or address.startswith('m') or address.startswith('n'):
            return True
        
        return False


    def validate_ethereum_address(self, address):
        """Validate Ethereum"""
        address = address.strip()
        if not address.startswith('0x'):
            return False
        if len(address) != 42:
            return False
        try:
            int(address[2:], 16)
            return True
        except:
            return False
    

    def validate_xrp_address(self, address):
        """Validate XRP """
        address = address.strip()
        if not address.startswith('r'):
            return False
        if len(address) < 25 or len(address) > 35:
            return False
        if not re.match(r'^r[1-9A-HJ-NP-Za-km-z]{24,33}$', address):
            return False
        return True
    

    def validate_solana_address(self, address):
        """Validate Solana"""
        address = address.strip()
        if len(address) < 32 or len(address) > 44:
            return False
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
            return False
        return True
    

    def fetch_balance(self, crypto, address):
        """Fetch balance for specific wallet"""
        config = CRYPTO_CONFIGS[crypto]
        
        try:
            if crypto == Cryptocurrency.BITCOIN:
                api_url = f"https://blockchain.info/rawaddr/{address}"
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    balance = data.get('final_balance', 0) / (10 ** config['decimals'])
                    total_received = data.get('total_received', 0) / (10 ** config['decimals'])
                    total_sent = data.get('total_sent', 0) / (10 ** config['decimals'])
                    tx_count = data.get('n_tx', 0)
                    
                    return {
                        'balance': balance,
                        'total_received': total_received,
                        'total_sent': total_sent,
                        'transaction_count': tx_count,
                        'raw_data': data
                    }
                else:
                    self.show_error(f"Failed to fetch Bitcoin balance. Status code: {response.status_code}")
            
            elif crypto == Cryptocurrency.ETHEREUM:
                api_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        balance = int(data.get('result', 0)) / (10 ** config['decimals'])
                        
                        tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc"
                        tx_response = self.session.get(tx_url, timeout=10)
                        tx_count = 0
                        if tx_response.status_code == 200:
                            tx_data = tx_response.json()
                            tx_count = len(tx_data.get('result', []))
                        
                        return {
                            'balance': balance,
                            'total_received': None,
                            'total_sent': None,
                            'transaction_count': tx_count,
                            'raw_data': data
                        }
                    else:
                        self.show_error(f"Etherscan API error: {data.get('message', 'Unknown error')}")
                else:
                    self.show_error(f"Failed to fetch Ethereum balance. Status code: {response.status_code}")
            
            elif crypto == Cryptocurrency.XRP:
                url = f"{config['api_base']}/account/{address}"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    balance = float(data.get('xrpBalance', 0))
                    
                    return {
                        'balance': balance,
                        'total_received': None,
                        'total_sent': None,
                        'transaction_count': data.get('transactions', 0),
                        'raw_data': data
                    }
                else:
                    self.show_error(f"Failed to fetch XRP balance. Status code: {response.status_code}")
            
            elif crypto == Cryptocurrency.SOLANA:
                url = f"{config['api_base']}/account/{address}"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    balance = data.get('lamports', 0) / (10 ** config['decimals'])
                    
                    return {
                        'balance': balance,
                        'total_received': None,
                        'total_sent': None,
                        'transaction_count': data.get('transactionCount', 0),
                        'raw_data': data
                    }
                else:
                    self.show_error(f"Failed to fetch Solana balance. Status code: {response.status_code}")
        
        except requests.exceptions.Timeout:
            self.show_error(f"Timeout while fetching {crypto.name} balance. Please try again.")
        except requests.exceptions.ConnectionError:
            self.show_error(f"Connection error while fetching {crypto.name} balance. Check your internet connection.")
        except Exception as e:
            self.show_error(f"Error fetching {crypto.name} balance: {str(e)}")
        return None
    
    
    def fetch_transactions(self, crypto, address, limit=500):
        """Fetch transactions for specific coin"""
        config = CRYPTO_CONFIGS[crypto]
        transactions = []
        
        try:
            if crypto == Cryptocurrency.BITCOIN:
                url = f"https://blockchain.info/rawaddr/{address}?limit={limit}"
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for tx in data.get('txs', []):
                        tx_data = self._parse_bitcoin_tx(tx, address, config)
                        if tx_data:
                            transactions.append(tx_data)
                    if not transactions:
                        self.show_error(f"No Bitcoin transactions found for address: {address}")
                else:
                    self.show_error(f"Failed to fetch Bitcoin transactions. Status code: {response.status_code}")
            
            elif crypto == Cryptocurrency.ETHEREUM:
                url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&page=1&offset={limit}"
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        for tx in data.get('result', []):
                            tx_data = self._parse_ethereum_tx(tx, address, config)
                            if tx_data:
                                transactions.append(tx_data)
                        if not transactions:
                            self.show_error(f"No Ethereum transactions found for address: {address}")
                    else:
                        self.show_error(f"Etherscan API error: {data.get('message', 'Unknown error')}")
                else:
                    self.show_error(f"Failed to fetch Ethereum transactions. Status code: {response.status_code}")
            
            elif crypto == Cryptocurrency.XRP:
                url = f"{config['api_base']}/account/{address}/transactions"
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for tx in data.get('transactions', []):
                        tx_data = self._parse_xrp_tx(tx, address, config)
                        if tx_data:
                            transactions.append(tx_data)
                    if not transactions:
                        self.show_error(f"No XRP transactions found for address: {address}")
                else:
                    self.show_error(f"Failed to fetch XRP transactions. Status code: {response.status_code}")
            
            elif crypto == Cryptocurrency.SOLANA:
                url = f"{config['api_base']}/account/transactions?account={address}&limit={limit}"
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for tx in data:
                        tx_data = self._parse_solana_tx(tx, address, config)
                        if tx_data:
                            transactions.append(tx_data)
                    if not transactions:
                        self.show_error(f"No Solana transactions found for address: {address}")
                else:
                    self.show_error(f"Failed to fetch Solana transactions. Status code: {response.status_code}")
        
        except requests.exceptions.Timeout:
            self.show_error(f"Timeout while fetching {crypto.name} transactions. Please try again.")
        except requests.exceptions.ConnectionError:
            self.show_error(f"Connection error while fetching {crypto.name} transactions. Check your internet connection.")
        except Exception as e:
            self.show_error(f"Error fetching {crypto.name} transactions: {str(e)}")
        return transactions[:limit]
    

    
    def _parse_bitcoin_tx(self, tx, address, config):
        """get Bitcoin transaction from blockchain.info"""
        try:
            timestamp = datetime.fromtimestamp(tx.get('time', 0))
            tx_hash = tx.get('hash', '')
            
            amount = 0
            tx_type = 'unknown'
            
            is_sender = False
            for inp in tx.get('inputs', []):
                prev_out = inp.get('prev_out', {})
                if prev_out.get('addr') == address:
                    is_sender = True
            
            for out in tx.get('out', []):
                if out.get('addr') == address:
                    amount += out.get('value', 0) / (10 ** config['decimals'])
            
            if is_sender:
                total_sent = 0
                for out in tx.get('out', []):
                    if out.get('addr') != address:
                        total_sent += out.get('value', 0) / (10 ** config['decimals'])
                amount = -total_sent
                tx_type = 'sent'
            else:
                tx_type = 'received'
            
            return {
                'hash': tx_hash,
                'timestamp': timestamp,
                'amount': amount,
                'type': tx_type,
                'fee': tx.get('fee', 0) / (10 ** config['decimals']),
                'confirmations': tx.get('block_height', 'pending'),
                'raw_data': tx
            }
        
        except Exception as e:
            self.show_error(f"Error parsing Bitcoin transaction: {str(e)}")
            return None
    

    def _parse_ethereum_tx(self, tx, address, config):
        """get Ethereum transaction from Etherscan"""
        try:
            timestamp = datetime.fromtimestamp(int(tx.get('timeStamp', 0)))
            tx_hash = tx.get('hash', '')
            
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            address_lower = address.lower()
            
            amount = int(tx.get('value', 0)) / (10 ** config['decimals'])
            
            if from_addr == address_lower:
                tx_type = 'sent'
                amount = -amount
            elif to_addr == address_lower:
                tx_type = 'received'
            else:
                tx_type = 'interaction'
            
            gas_used = int(tx.get('gasUsed', 0))
            gas_price = int(tx.get('gasPrice', 0))
            fee = (gas_used * gas_price) / (10 ** config['decimals'])
            
            return {
                'hash': tx_hash,
                'timestamp': timestamp,
                'amount': amount,
                'type': tx_type,
                'fee': fee,
                'confirmations': int(tx.get('confirmations', 0)),
                'from': from_addr,
                'to': to_addr,
                'raw_data': tx
            }
        
        except Exception as e:
            self.show_error(f"Error parsing Ethereum transaction: {str(e)}")
            return None
        
    
    def _parse_xrp_tx(self, tx, address, config):
        """Pet XRP transaction"""
        try:
            timestamp = datetime.strptime(tx.get('date', ''), '%Y-%m-%dT%H:%M:%S%z') if tx.get('date') else datetime.now()
            tx_hash = tx.get('hash', '')
            
            amount = float(tx.get('Amount', 0)) / (10 ** config['decimals'])
            tx_type = 'received' if tx.get('Destination') == address else 'sent'
            
            if tx_type == 'sent':
                amount = -amount
            
            return {
                'hash': tx_hash,
                'timestamp': timestamp,
                'amount': amount,
                'type': tx_type,
                'fee': float(tx.get('Fee', 0)) / (10 ** config['decimals']),
                'confirmations': tx.get('ledger_index', 0),
                'raw_data': tx
            }
        
        except Exception as e:
            self.show_error(f"Error parsing XRP transaction: {str(e)}")
            return None
    
    def _parse_solana_tx(self, tx, address, config):
        """get Solana transaction"""
        try:
            timestamp = datetime.fromtimestamp(tx.get('blockTime', 0))
            tx_hash = tx.get('txHash', '')
            
            return {
                'hash': tx_hash,
                'timestamp': timestamp,
                'amount': 0,
                'type': 'unknown',
                'fee': tx.get('fee', 0) / (10 ** config['decimals']),
                'confirmations': 1,
                'raw_data': tx
            }
        
        except Exception as e:
            self.show_error(f"Error parsing Solana transaction: {str(e)}")
            return None


class MoneyFlowAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("MoneyFlow")
        
        # Window size and position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.85)
        self.root.geometry(f"{window_width}x{window_height}")
        
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # vars
        self.address = tk.StringVar()
        self.crypto_var = tk.StringVar(value="Bitcoin (BTC)")
        self.transaction_limit = 2000
        self.transactions_data = []
        self.stats_labels = {}
        self.status_var = tk.StringVar(value="Ready. Select cryptocurrency and enter address.")
        self.current_prices = {}
        self.full_txids = {}
        self.current_fig = None
        self.current_canvas = None
        self.api_handler = MultiCryptoAPI(error_callback=self.show_api_error)
        
        self.setup_styles()
        self.setup_gui()
        threading.Thread(target=self.fetch_all_prices, daemon=True).start()
        

    # styles for ui
    def setup_styles(self):
        """Setup application styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.bg_color = "#0a0a0a"
        self.fg_color = "#e0e0e0"
        self.card_bg = "#151515"
        self.border_color = "#404040"
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=('Segoe UI', 10))
        style.configure("TButton", background=self.card_bg, foreground=self.fg_color, font=('Segoe UI', 10))
        style.configure("TEntry", fieldbackground=self.card_bg, foreground=self.fg_color, font=('Segoe UI', 10))
        style.configure("TCombobox", fieldbackground=self.card_bg, foreground=self.fg_color)
        style.map('TCombobox', fieldbackground=[('readonly', self.card_bg)])
    

    # gui layout 
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        border_frame = ttk.Frame(main_frame, borderwidth=2, relief="solid")
        border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        content_frame = ttk.Frame(border_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Control Panel
        control_frame = ttk.Frame(content_frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(control_frame, text="Cryptocurrency:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.crypto_combo = ttk.Combobox(control_frame, textvariable=self.crypto_var, 
                                        values=["Bitcoin (BTC)", "Ethereum (ETH)", "XRP (XRP)", "Solana (SOL)"],
                                        state="readonly", width=15)
        self.crypto_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.crypto_combo.current(0)
        self.crypto_combo.bind('<<ComboboxSelected>>', self.on_crypto_change)
        
        ttk.Label(control_frame, text="Address:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.address_entry = ttk.Entry(control_frame, textvariable=self.address, width=50)
        self.address_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        analyze_btn = ttk.Button(control_frame, text="Analyze", command=self.analyze_address)
        analyze_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(control_frame, text="Clear", command=self.clear_data)
        clear_btn.pack(side=tk.LEFT)
        
        # Row with Coin Prices
        stats_frame = ttk.Frame(content_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 12))
        
        stats_info = [
            ("Cryptocurrency:", "crypto_name"),
            ("Balance:", "balance"),
            ("Transactions:", "tx_count"),
            ("Value USD:", "value_usd"),
            ("First Tx:", "first_tx"),
            ("Last Tx:", "last_tx")
        ]
        
        for i, (label_text, key) in enumerate(stats_info):
            stat_container = ttk.Frame(stats_frame)
            stat_container.pack(side=tk.LEFT, padx=(0, 25))
            
            ttk.Label(stat_container, text=label_text, font=('Segoe UI', 9)).pack(side=tk.LEFT)
            self.stats_labels[key] = ttk.Label(stat_container, text="-", font=('Segoe UI', 9, 'bold'))
            self.stats_labels[key].pack(side=tk.LEFT, padx=(3, 0))
        
        ttk.Label(stats_frame, text="", font=('Segoe UI', 9)).pack(side=tk.LEFT, expand=True)
        
        prices_group = ttk.Frame(stats_frame)
        prices_group.pack(side=tk.LEFT)
        
        self.price_labels = {}
        cryptos = ['bitcoin', 'ethereum', 'ripple', 'solana']
        for crypto in cryptos:
            label = ttk.Label(prices_group, text=f"{crypto.title()}: $--", 
                            font=('Segoe UI', 9))
            label.pack(side=tk.LEFT, padx=(0, 15))
            self.price_labels[crypto] = label
        
        ttk.Label(stats_frame, text="", font=('Segoe UI', 9)).pack(side=tk.LEFT, expand=True)
        
        # Content Panels
        content_paned = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL, 
                                      sashwidth=8, sashrelief=tk.RAISED, bg=self.bg_color)
        content_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel - Transactions
        left_frame = ttk.Frame(content_paned)
        content_paned.add(left_frame)
        
        # Transaction list
        self.transaction_tree = self.create_transaction_tree(left_frame)
        
        # Right Panel - Money Flow Graph
        right_frame = ttk.Frame(content_paned)
        content_paned.add(right_frame)
        
        # Graph header
        graph_header = ttk.Frame(right_frame)
        graph_header.pack(fill=tk.X, pady=(0, 8))
        
        self.graph_title = ttk.Label(graph_header, text="Money Flow Analysis", 
                                    font=('Segoe UI', 10, 'bold'))
        self.graph_title.pack(expand=True)
        
        # Graph frame
        self.graph_frame = ttk.Frame(right_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_bar = ttk.Frame(content_frame, relief=tk.SUNKEN, height=24)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        status_bar.pack_propagate(False)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_bar, variable=self.progress_var, 
                                           mode='indeterminate', length=180)
        self.progress_bar.pack(side=tk.RIGHT, padx=8, pady=2)
        
        status_label = ttk.Label(status_bar, textvariable=self.status_var, font=('Segoe UI', 9))
        status_label.pack(side=tk.LEFT, padx=8, pady=2)
        
        content_paned.bind('<Button-1>', lambda e: 'break')


    def on_crypto_change(self, event=None):
        """Handle cryptocurrency selection change"""
        selected = self.crypto_var.get()
        crypto_name = selected.split(" (")[0] if "(" in selected else selected
        
        crypto = self.get_current_crypto()
        config = CRYPTO_CONFIGS[crypto]
        
        # Update crypto name in stats with color
        if 'crypto_name' in self.stats_labels:
            for widget in self.stats_labels['crypto_name'].master.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.destroy()
            
            colored_label = tk.Label(self.stats_labels['crypto_name'].master, 
                                   text=config['name'], 
                                   font=('Segoe UI', 9, 'bold'),
                                   bg=self.bg_color, 
                                   fg=config['color'])
            colored_label.pack(side=tk.LEFT, padx=(3, 0))
            self.stats_labels['crypto_name'] = colored_label
        
        self.status_var.set(f"Selected: {crypto_name}")
        
        if self.address.get():
            self.transaction_tree.delete(*self.transaction_tree.get_children())
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
            self.status_var.set(f"Ready to analyze {crypto_name} address")


    def create_transaction_tree(self, parent):
        """Create transaction treeview with scrollbar"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Time', 'Type', 'Amount', 'USD Value', 'Hash')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # column widths
        tree.column('Time', width=150, anchor=tk.W)
        tree.column('Type', width=100, anchor=tk.CENTER)
        tree.column('Amount', width=150, anchor=tk.E)
        tree.column('USD Value', width=120, anchor=tk.E)
        tree.column('Hash', width=300, anchor=tk.W)
        
        # column headings
        for col in columns:
            tree.heading(col, text=col)

        # Orange for interactions, greece = received , red =sent 
        tree.tag_configure('sent', foreground='#FF4444')  
        tree.tag_configure('received', foreground='#44FF44') 
        tree.tag_configure('interaction', foreground='#FFAA44')  
        
        # scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        tree.bind('<Button-1>', self.on_tree_click)
        tree.bind('<Double-1>', self.on_tree_double_click)
    
        return tree
    
    
    def fetch_all_prices(self):
        """Fetch current prices for all cryptocurrencies with fallback options"""
        attempts = [
            ("CoinGecko", self.fetch_coingecko_prices),
            ("CoinMarketCap", self.fetch_coinmarketcap_prices),
            ("CoinPaprika", self.fetch_coinpaprika_prices)
        ]
        
        for attempt_name, fetch_func in attempts:
            try:
                self.root.after(0, lambda: self.status_var.set(f"Fetching prices from {attempt_name}..."))
                prices, error = fetch_func()
                if prices:
                    self.current_prices = prices
                    self.root.after(0, self.update_price_labels)
                    self.root.after(0, lambda: self.status_var.set("Prices updated successfully"))
                    return
                else:
                    self.show_price_error(f"Failed to fetch from {attempt_name}: {error}")
            except Exception as e:
                self.show_price_error(f"Error with {attempt_name}: {str(e)}")
            time.sleep(2)  
        

        # If all attempts fail, use hardcoded recent prices (Feb 5, 2026 estimates)
        self.show_price_error("All price fetch attempts failed. Using estimated recent prices.")

        # 5/2/2026 prices 
        self.current_prices = {
            'bitcoin': 69589,  
            'ethereum': 2770,   
            'ripple': 1.36,      
            'solana': 90      
        }
        self.root.after(0, self.update_price_labels)
    

    def fetch_coingecko_prices(self):
        """Fetch prices from CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,ripple,solana',
                'vs_currencies': 'usd'
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                prices = {
                    'bitcoin': data.get('bitcoin', {}).get('usd', 0),
                    'ethereum': data.get('ethereum', {}).get('usd', 0),
                    'ripple': data.get('ripple', {}).get('usd', 0),
                    'solana': data.get('solana', {}).get('usd', 0)
                }
                return prices, None
            else:
                return None, f"Status code: {response.status_code}"
        except Exception as e:
            return None, str(e)


    def fetch_coinmarketcap_prices(self):
        """Fetch prices from CoinMarketCap (free tier)"""
        try:
            url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing"
            params = {
                'start': '1',
                'limit': '100',
                'sortBy': 'market_cap',
                'sortType': 'desc',
                'convert': 'USD'
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for coin in data.get('data', {}).get('cryptoCurrencyList', []):
                    symbol = coin.get('symbol', '').lower()
                    if symbol == 'btc':
                        prices['bitcoin'] = coin.get('quotes', [{}])[0].get('price', 0)
                    elif symbol == 'eth':
                        prices['ethereum'] = coin.get('quotes', [{}])[0].get('price', 0)
                    elif symbol == 'xrp':
                        prices['ripple'] = coin.get('quotes', [{}])[0].get('price', 0)
                    elif symbol == 'sol':
                        prices['solana'] = coin.get('quotes', [{}])[0].get('price', 0)
                
                # Check if we got all prices
                required = ['bitcoin', 'ethereum', 'ripple', 'solana']
                if all(req in prices for req in required):
                    return prices, None
                else:
                    return None, "Missing some coin prices"
            else:
                return None, f"Status code: {response.status_code}"
        except Exception as e:
            return None, str(e)
        
    
    def fetch_coinpaprika_prices(self):
        """Fetch prices from CoinPaprika"""
        try:
            url = "https://api.coinpaprika.com/v1/tickers"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for coin in data:
                    symbol = coin.get('symbol', '').lower()
                    if symbol == 'btc':
                        prices['bitcoin'] = coin.get('quotes', {}).get('USD', {}).get('price', 0)
                    elif symbol == 'eth':
                        prices['ethereum'] = coin.get('quotes', {}).get('USD', {}).get('price', 0)
                    elif symbol == 'xrp':
                        prices['ripple'] = coin.get('quotes', {}).get('USD', {}).get('price', 0)
                    elif symbol == 'sol':
                        prices['solana'] = coin.get('quotes', {}).get('USD', {}).get('price', 0)
                
                # Check if we got all prices
                required = ['bitcoin', 'ethereum', 'ripple', 'solana']
                if all(req in prices for req in required):
                    return prices, None
                else:
                    return None, "Missing some coin prices"
            else:
                return None, f"Status code: {response.status_code}"
        except Exception as e:
            return None, str(e)
        
    
    def update_price_labels(self):
        for crypto, price in self.current_prices.items():
            if crypto in self.price_labels:
                display_name = crypto.title()
                if crypto == 'ripple':
                    display_name = 'XRP'
                self.price_labels[crypto].config(
                    text=f"{display_name}: ${price:,.2f}"
                )
    
    def show_price_error(self, message):
        """Show price fetch errors in status bar and messagebox"""
        self.root.after(0, lambda: self.status_var.set(f"Price Error: {message}"))
        self.root.after(0, lambda: messagebox.showwarning(
            "Price Fetch Warning", 
            f"{message}\n\nUsing estimated prices for calculations."
        ))

    
    def show_api_error(self, message):
        """Show API error from MultiCryptoAPI"""
        self.root.after(0, lambda: messagebox.showerror("API Error", message))
        self.root.after(0, lambda: self.status_var.set(f"API Error: {message}"))
    
    def get_current_crypto(self):
        selected = self.crypto_var.get()
        if selected == "Bitcoin (BTC)":
            return Cryptocurrency.BITCOIN
        elif selected == "Ethereum (ETH)":
            return Cryptocurrency.ETHEREUM
        elif selected == "XRP (XRP)":
            return Cryptocurrency.XRP
        elif selected == "Solana (SOL)":
            return Cryptocurrency.SOLANA
        return Cryptocurrency.BITCOIN
    

    def analyze_address(self):
        """Main analysis function"""
        address = self.address.get().strip()
        if not address:
            messagebox.showwarning("Input Error", "Please enter a cryptocurrency address")
            return
        
        crypto = self.get_current_crypto()
        config = CRYPTO_CONFIGS[crypto]
        
        if not self.api_handler.validate_address(crypto, address):
            messagebox.showerror("Invalid Address", 
                                f"Invalid {config['name']} address.\n"
                                f"Please check and try again.")
            return
        
        self.transaction_tree.delete(*self.transaction_tree.get_children())
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        if 'crypto_name' in self.stats_labels:
            for widget in self.stats_labels['crypto_name'].master.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.destroy()
            
            colored_label = tk.Label(self.stats_labels['crypto_name'].master, 
                                   text=config['name'], 
                                   font=('Segoe UI', 9, 'bold'),
                                   bg=self.bg_color, 
                                   fg=config['color'])
            colored_label.pack(side=tk.LEFT, padx=(3, 0))
            self.stats_labels['crypto_name'] = colored_label
        
        self.status_var.set(f"Analyzing {config['name']} address...")
        self.progress_bar.start()
        
        threading.Thread(target=self.perform_analysis, args=(crypto, address), daemon=True).start()
    


    def perform_analysis(self, crypto, address):
        """Perform analysis in background thread"""
        try:
            config = CRYPTO_CONFIGS[crypto]
            
            # Fetch balance
            self.root.after(0, lambda: self.status_var.set("Fetching balance..."))
            balance_data = self.api_handler.fetch_balance(crypto, address)
            
            if not balance_data:
                self.root.after(0, lambda: self.show_error(f"Failed to fetch balance for {config['name']} address"))
                return
            
            # Fetch transactions
            self.root.after(0, lambda: self.status_var.set("Fetching transactions..."))
            transactions = self.api_handler.fetch_transactions(crypto, address, self.transaction_limit)
            
            if not transactions:
                self.root.after(0, self.show_error, f"No transactions found for this {config['name']} address")
                return
            
            # Get current price - use correct coingecko key
            coingecko_key = crypto.value  # 'bitcoin', 'ethereum', 'ripple', 'solana'
            crypto_price = self.current_prices.get(coingecko_key, 0)
            balance_usd = balance_data['balance'] * crypto_price
            
            # Update display
            self.root.after(0, self.update_display, crypto, address, balance_data, transactions, crypto_price, balance_usd)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Analysis error: {str(e)}")
    


    def update_display(self, crypto, address, balance_data, transactions, price, balance_usd):
        """Update the GUI with analysis results"""
        try:
            config = CRYPTO_CONFIGS[crypto]
            symbol = config['symbol']
            
            # Update statistics
            self.stats_labels['balance'].config(text=f"{balance_data['balance']:.6f} {symbol}")
            self.stats_labels['tx_count'].config(text=str(balance_data['transaction_count']))
            self.stats_labels['value_usd'].config(text=f"${balance_usd:,.2f}")
            
            if transactions:
                dates = [tx['timestamp'] for tx in transactions if isinstance(tx['timestamp'], datetime)]
                if dates:
                    first_tx = min(dates).strftime('%Y-%m-%d')
                    last_tx = max(dates).strftime('%Y-%m-%d')
                    self.stats_labels['first_tx'].config(text=first_tx)
                    self.stats_labels['last_tx'].config(text=last_tx)
                else:
                    self.stats_labels['first_tx'].config(text="Unknown")
                    self.stats_labels['last_tx'].config(text="Unknown")
            else:
                self.stats_labels['first_tx'].config(text="No tx")
                self.stats_labels['last_tx'].config(text="No tx")
            
            self.transactions_data = []
            
            # Add transactions to treeview
            for tx in transactions:
                tx_hash = tx.get('hash', 'Unknown')[:64]
                
                timestamp = tx.get('timestamp', datetime.now())
                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime('%Y-%m-%d %H:%M')
                else:
                    time_str = str(timestamp)
                
                amount = tx.get('amount', 0)
                tx_type = tx.get('type', 'unknown').lower()
                
                usd_amount = abs(amount) * price if price > 0 else 0
                
                amount_formatted = f"{amount:+.8f} {symbol}" if amount != 0 else f"0.00000000 {symbol}"
                usd_formatted = f"${usd_amount:,.2f}" if usd_amount > 0 else "$0.00"
                
                if len(tx_hash) > 40:
                    hash_display = tx_hash[:40] + "..."
                else:
                    hash_display = tx_hash
                
                tags = ()
                if tx_type == 'sent':
                    tags = ('sent',)
                elif tx_type == 'received':
                    tags = ('received',)
                elif tx_type == 'interaction':
                    tags = ('interaction',)
                
                item_id = self.transaction_tree.insert('', tk.END, values=(
                    time_str,
                    tx_type.capitalize(),
                    amount_formatted,
                    usd_formatted,
                    hash_display
                ), tags=tags)
                
                self.full_txids[item_id] = tx_hash
                
                self.transactions_data.append({
                    'hash': tx_hash,
                    'type': tx_type,
                    'amount': amount,
                    'timestamp': time_str,
                    'address': address,
                    'full_tx_data': tx
                })
            
            # Create money flow graph
            self.create_money_flow_graph(crypto)
            
            self.status_var.set(f"Analysis complete. Found {balance_data['transaction_count']} transactions")
            self.progress_bar.stop()
            
        except Exception as e:
            self.show_error(f"Error processing data: {str(e)}")
            self.progress_bar.stop()
    

    def create_money_flow_graph(self, crypto):
        """Create the money flow graph visualization"""
        if not self.transactions_data:
            no_data_label = ttk.Label(self.graph_frame, text="No transaction data available", font=('Segoe UI', 12))
            no_data_label.pack(expand=True)
            return    
        try:
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
            
            config = CRYPTO_CONFIGS[crypto]
            
            self.current_fig = plt.figure(figsize=(12, 10))
            ax = self.current_fig.add_subplot(111)
            
            G = nx.DiGraph()
            
            crypto_color = config['color']
            G.add_node("Target", size=1400, color=crypto_color, label=f"Target\n({config['symbol']})")
            
            # Add transaction nodes (green for received, red for sent)
            max_nodes = min(15, len(self.transactions_data))
            for i, tx in enumerate(self.transactions_data[:max_nodes]):
                node_id = f"Tx{i+1}"
                node_color = "#44FF44" if tx['type'] == 'received' else "#FF4444"
                G.add_node(node_id, size=600, color=node_color, label=f"Tx{i+1}")
                
                if tx['type'] == 'received':
                    G.add_edge("Source", node_id, weight=abs(tx['amount']))
                    G.add_edge(node_id, "Target", weight=abs(tx['amount']))
                elif tx['type'] == 'sent':
                    G.add_edge("Target", node_id, weight=abs(tx['amount']))
                    G.add_edge(node_id, "Destination", weight=abs(tx['amount']))

            # colors for nodes 
            G.add_node("Source", size=800, color="#44FF44", label="Sources")  
            G.add_node("Destination", size=800, color="#FF4444", label="Destinations") 
            
            try:
                pos = nx.spring_layout(G, k=1.5, iterations=100, seed=42)
            except:
                pos = nx.circular_layout(G)
            
            node_colors = [G.nodes[n]['color'] for n in G.nodes()]
            node_sizes = [G.nodes[n]['size'] for n in G.nodes()]
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                                 alpha=0.85, ax=ax, linewidths=0.5, edgecolors='white')
            
            if G.edges():
                edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
                if edge_weights:
                    max_weight = max(edge_weights)
                    edge_widths = [0.5 + (w / max_weight * 2) for w in edge_weights]
                else:
                    edge_widths = [1] * len(G.edges())
                
                nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6, edge_color='#666666', 
                                      arrows=True, arrowsize=8, arrowstyle='->', ax=ax, 
                                      connectionstyle='arc3,rad=0.1')
            
            # Add labels
            labels = {n: G.nodes[n]['label'] for n in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax)
            ax.axis('off')

            # colors 2             
            legend_elements = [
                Patch(facecolor=crypto_color, label=f'Target Address ({config["symbol"]})'),
                Patch(facecolor="#44FF44", label='Incoming Transactions (Received)'),
                Patch(facecolor="#FF4444", label='Outgoing Transactions (Sent)'),
            ]
            ax.legend(handles=legend_elements, loc='upper left', framealpha=0.3)
            plt.tight_layout()
            
            container = ttk.Frame(self.graph_frame)
            container.pack(fill=tk.BOTH, expand=True)
            
            self.current_canvas = FigureCanvasTkAgg(self.current_fig, container)
            self.current_canvas.draw()
            
            class CustomToolbar(NavigationToolbar2Tk):
                def __init__(self, canvas, parent, analyzer):
                    NavigationToolbar2Tk.__init__(self, canvas, parent)
                    self.analyzer = analyzer
                    
                    save_button_index = -1
                    for i, child in enumerate(self.winfo_children()):
                        if isinstance(child, tk.Button) and 'Save' in child.cget('text'):
                            save_button_index = i
                            break
                    
                    self.refresh_btn = tk.Button(self, text="Refresh Graph", 
                                                command=self.refresh_graph,
                                                bg="#404040", fg="white",
                                                relief=tk.RAISED, bd=1,
                                                padx=5, pady=2,
                                                font=('Segoe UI', 9))
                    
                    self.flow_details_btn = tk.Button(self, text="📊 Flow Details", 
                                                     command=self.show_flow_details,
                                                     bg="#404040", fg="white",
                                                     relief=tk.RAISED, bd=1,
                                                     padx=5, pady=2,
                                                     font=('Segoe UI', 9))
                    
                    if save_button_index != -1:
                        after_save_widget = None
                        for i, child in enumerate(self.winfo_children()):
                            if i > save_button_index:
                                after_save_widget = child
                                break
                        
                        if after_save_widget:
                            self.refresh_btn.pack(side=tk.LEFT, before=after_save_widget, padx=(2, 2))
                            self.flow_details_btn.pack(side=tk.LEFT, before=after_save_widget, padx=(2, 2))
                        else:
                            self.refresh_btn.pack(side=tk.LEFT, padx=(2, 2))
                            self.flow_details_btn.pack(side=tk.LEFT, padx=(2, 2))
                    else:
                        self.refresh_btn.pack(side=tk.LEFT, padx=(2, 2))
                        self.flow_details_btn.pack(side=tk.LEFT, padx=(2, 2))
                
                def refresh_graph(self):
                    self.analyzer.refresh_graph()
                
                def show_flow_details(self):
                    self.analyzer.show_flow_details()
            
            toolbar = CustomToolbar(self.current_canvas, container, self)
            toolbar.update()
            
            self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            toolbar.pack(fill=tk.X)
            

        except Exception as e:
            error_label = ttk.Label(self.graph_frame, text=f"Error creating graph: {str(e)}", 
                                   font=('Segoe UI', 10), foreground="#FF6B6B")
            error_label.pack(expand=True)
            messagebox.showerror("Graph Error", f"Failed to create money flow graph: {str(e)}")
    

    def refresh_graph(self):
        if self.transactions_data:
            crypto = self.get_current_crypto()
            self.create_money_flow_graph(crypto)

    
    def clear_data(self):
        self.address.set("")
        self.transaction_tree.delete(*self.transaction_tree.get_children())
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        for key in self.stats_labels:
            if key != 'crypto_name':
                self.stats_labels[key].config(text="-", foreground=self.fg_color)
        
        if 'crypto_name' in self.stats_labels:
            for widget in self.stats_labels['crypto_name'].master.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.destroy()
            
            default_label = tk.Label(self.stats_labels['crypto_name'].master, 
                                   text="-", 
                                   font=('Segoe UI', 9, 'bold'),
                                   bg=self.bg_color, 
                                   fg=self.fg_color)
            default_label.pack(side=tk.LEFT, padx=(3, 0))
            self.stats_labels['crypto_name'] = default_label
        
        self.full_txids.clear()
        
        self.status_var.set("Ready. Select cryptocurrency and enter address.")
        self.progress_bar.stop()
    

    def on_tree_click(self, event):
        region = self.transaction_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.transaction_tree.identify_row(event.y)
            column = self.transaction_tree.identify_column(event.x)
    

    def on_tree_double_click(self, event):
        region = self.transaction_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.transaction_tree.identify_row(event.y)
            column = self.transaction_tree.identify_column(event.x)
            
            if item and column:
                col_index = int(column.replace('#', '')) - 1
                columns = self.transaction_tree['columns']
                if col_index < len(columns):
                    col_name = columns[col_index]
                    values = self.transaction_tree.item(item, 'values')
                    
                    if col_name == 'Hash' and item in self.full_txids:
                        value_to_copy = self.full_txids[item]
                    else:
                        value_to_copy = values[col_index] if col_index < len(values) else ""
                    
                    try:
                        pyperclip.copy(str(value_to_copy))
                        display_text = str(value_to_copy)[:30]
                        if len(str(value_to_copy)) > 30:
                            display_text += "..."
                        self.status_var.set(f"Copied: {display_text}")
                    except Exception as e:
                        try:
                            self.root.clipboard_clear()
                            self.root.clipboard_append(str(value_to_copy))
                            self.status_var.set(f"Copied: {str(value_to_copy)[:30]}...")
                        except:
                            self.status_var.set("Failed to copy to clipboard")
    

    def show_flow_details(self):
        """Show flow analysis window"""
        if not self.transactions_data:
            messagebox.showinfo("No Data", "No transaction data available to analyze.")
            return
        
        crypto = self.get_current_crypto()
        config = CRYPTO_CONFIGS[crypto]
        
        details_window = tk.Toplevel(self.root)
        details_window.title(f"{config['name']} Detailed Flow Analysis")
        details_window.geometry("1200x800")
        
        details_window.update_idletasks()
        width = details_window.winfo_width()
        height = details_window.winfo_height()
        x = (details_window.winfo_screenwidth() // 2) - (width // 2)
        y = (details_window.winfo_screenheight() // 2) - (height // 2)
        details_window.geometry(f'{width}x{height}+{x}+{y}')
        
        main_container = ttk.Frame(details_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title with crypto color
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, text=f"{config['name']} ADDRESS-TO-ADDRESS MONEY FLOW", 
                              font=('Segoe UI', 14, 'bold'), 
                              bg=self.bg_color,
                              fg=config['color'])
        title_label.pack()
        
        ttk.Label(title_frame, text=f"Target Address: {self.address.get().strip()}", 
                 font=('Segoe UI', 10)).pack()
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Flow Analysis tab
        flow_frame = ttk.Frame(notebook)
        notebook.add(flow_frame, text="Flow Analysis")
        
        flow_text = scrolledtext.ScrolledText(flow_frame, wrap=tk.WORD, 
                                            font=('Courier New', 9),
                                            bg=self.card_bg, fg=self.fg_color,
                                            relief=tk.FLAT, borderwidth=2)
        flow_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics tab
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        
        stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, 
                                              font=('Courier New', 9),
                                              bg=self.card_bg, fg=self.fg_color,
                                              relief=tk.FLAT, borderwidth=2)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Generate analysis content
        flow_content, stats_content = self.generate_flow_analysis(crypto)
        
        flow_text.insert(tk.END, flow_content)
        stats_text.insert(tk.END, stats_content)
        
        flow_text.config(state=tk.DISABLED)
        stats_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        copy_flow_btn = ttk.Button(button_frame, text="Copy Flow Analysis", 
                                  command=lambda: self.copy_to_clipboard(flow_content))
        copy_flow_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = ttk.Button(button_frame, text="Close", command=details_window.destroy)
        close_btn.pack(side=tk.RIGHT)


    def generate_flow_analysis(self, crypto):
        """Generate flow analysis text"""
        if not self.transactions_data:
            return "No transaction data available.", "No statistics available."
        
        config = CRYPTO_CONFIGS[crypto]
        target_address = self.address.get().strip()
        # Get price using correct coingecko key
        coingecko_key = crypto.value
        crypto_price = self.current_prices.get(coingecko_key, 0)
        
        flow = []
        flow.append(f"{config['name']} Money Flow analysis \n")
        flow.append("-" * 60)
        flow.append(f"Target Address: {target_address}")
        flow.append(f"Cryptocurrency: {config['name']} ({config['symbol']})")
        flow.append(f"Current Price: ${crypto_price:,.2f}")
        flow.append(f"Total Transactions Analyzed: {len(self.transactions_data)}")
        flow.append("-" * 60 + "\n")
        
        # lists 
        incoming_txs = [tx for tx in self.transactions_data if tx['type'] == 'received']
        outgoing_txs = [tx for tx in self.transactions_data if tx['type'] == 'sent']
        total_incoming = sum(tx['amount'] for tx in incoming_txs if tx['amount'] > 0)
        total_outgoing = sum(abs(tx['amount']) for tx in outgoing_txs if tx['amount'] < 0)
        
        flow.append(f"Incoming Transactions: {len(incoming_txs)}")
        flow.append(f"Total Received: {total_incoming:.8f} {config['symbol']}")
        flow.append(f"Value: ${total_incoming * crypto_price:,.2f}")
        flow.append(f"\nOutgoing Transactions: {len(outgoing_txs)}")
        flow.append(f"Total Sent: {total_outgoing:.8f} {config['symbol']}")
        flow.append(f"Value: ${total_outgoing * crypto_price:,.2f}")
        
        # Show all transactions
        flow.append("\n" + "=" * 60)
        flow.append(f"All Transactions ({len(self.transactions_data)} total)")
        flow.append("=" * 60)
        
        for i, tx in enumerate(self.transactions_data, 1):
            flow.append(f"\n{i}. {tx['type'].upper()}: {abs(tx['amount']):.8f} {config['symbol']}")
            flow.append(f"   Date: {tx['timestamp']}")
            flow.append(f"   Value: ${abs(tx['amount']) * crypto_price:,.2f}")
            flow.append(f"   Hash: {tx['hash'][:50]}...")
        
        flow.append("\n" + "=" * 60)
        flow.append("END OF ANALYSIS")
        flow.append("=" * 60)
        
        # Statistics
        stats = []
        stats.append("=" * 80)
        stats.append(f"{config['name']} Stats")
        stats.append("=" * 80)
        stats.append(f"\nAddress: {target_address[:30]}...")
        stats.append(f"Network: {config['name']}")
        stats.append(f"Symbol: {config['symbol']}")
        stats.append(f"Decimals: {config['decimals']}")
        stats.append(f"Explorer: {config['explorer']}")
        stats.append("-" * 80)
        
        stats.append("\nTransaction Statistics:")
        stats.append(f"Total Transactions: {len(self.transactions_data)}")
        stats.append(f"Incoming Transactions: {len(incoming_txs)}")
        stats.append(f"Outgoing Transactions: {len(outgoing_txs)}")
        
        if self.transactions_data:
            amounts = [tx['amount'] for tx in self.transactions_data]
            positive_amounts = [a for a in amounts if a > 0]
            negative_amounts = [a for a in amounts if a < 0]
            
            stats.append(f"\nAmounts ({config['symbol']}):")
            if positive_amounts:
                stats.append(f"Largest Incoming: {max(positive_amounts):.8f}")
                stats.append(f"Average Incoming: {sum(positive_amounts)/len(positive_amounts):.8f}")
            if negative_amounts:
                stats.append(f"Largest Outgoing: {abs(min(negative_amounts)):.8f}")
                stats.append(f"Average Outgoing: {abs(sum(negative_amounts)/len(negative_amounts)):.8f}")
        
        stats.append(f"\nUSD values:")
        stats.append(f"Current Price: ${crypto_price:,.2f}")
        if total_incoming > 0:
            stats.append(f"Total Received Value: ${total_incoming * crypto_price:,.2f}")
        if total_outgoing > 0:
            stats.append(f"Total Sent Value: ${total_outgoing * crypto_price:,.2f}")
        
        return "\n".join(flow), "\n".join(stats)
    

    def copy_to_clipboard(self, text):
        # uses pyperclip 
        try:
            pyperclip.copy(text)
            messagebox.showinfo("Copied", "Analysis copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")
    

    def show_error(self, message):
        self.root.after(0, lambda: messagebox.showerror("Error", message))
        self.root.after(0, lambda: self.status_var.set(f"Error: {message}"))
        self.root.after(0, self.progress_bar.stop)


def main():
    root = tk.Tk()
    app = MoneyFlowAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()

# bc1qaa6ks0yz845wallrmlwn9ypp65p460w4cacwpp 