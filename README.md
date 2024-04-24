# tradingview_alram-mt5-multi_orders

imported txt file format:
usdeur=1.2,...

Descriptions: 
once occur alarm in TV, send it to metatrader5, and analyze logic from txt file, and then order
functionalities: 
revers: import txt file, reverse the types (e.g. sell => buy) 
comment: import txt file, allow comments (e.g. comment=10 (this comment exists in alarm of TV))
lot: in normal way, price = 0.1.  import txt file, price = 1.2 (e.g. usdeur=1.2)

tech:
Python Flask
