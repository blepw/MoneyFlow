MoneyFlow is a cyber intelligence tool designed for cryptocurrency transaction analysis and blockchain forensics . It shows where cryptocurrency is coming from and going to, helping spot suspicious patterns and connections between wallets. Useful for catching money laundering, fraud, and other shady crypto activity. 

Supports : Bitcoin , Ethereum , XRP & Solana 

--- 

## Interface 

![[moneyflow.png]]


![[flow_details.png]]

![[money_flow_graph.png]]

---


## How to Use 

* User chooses currency from the dropdown menu 
* Writes the address of any XRP, Solana , Bitcoin , Ethereum wallet 
* Clicks the button 'Analyze'

On the first section there will be a list of the money received and sent with the transaction hashes 

On the second section a graph will be generated to describe the flow of the transactions using nodes 

User can get more information by pressing the 'Flow details' button that will give more information about the transactions such as the total USD value , smallest , biggest transaction and the amount of transactions .

---

## How it works 

1 : The tool fetches data from blockchain explorers and API's to get 
Current balance , transaction history and price data from CoinGecko 

2: Processes the data to show . A transaction list , money flow graph 
and statistics 

3 : Visualizes by creating a network graph where the center is the target address
the green and the red arrows depict the money coming in & out and the lines show 
transaction paths 

---


## How to install & run


## 1 : Install Prerequisites using requirements.txt

```requirements.text
requests==2.31.0
matplotlib==3.7.5
networkx==3.2.1
pyperclip==1.8.2
tkinter==0.1.0
```

```bash
pip install -r requirements.txt
```

## 2 : Run

```python
python3 flow.py
```

---


## Project structure 

```text
flow/
├── flow.py
├── README.md
└── requirements.txt
```


---

## To do 

* Optimize code 
* Raise limits for fetching more transactions & visualize bigger nodes 
