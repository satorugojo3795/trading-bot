from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from alpaca_trade_api import REST
from timedelta import Timedelta
from ml_model import estimate_sentiment



API_KEY = "PKH7GY7YL14X86KSDS7Z"
API_SECRET = "2JL8alJYIzAxW7LKGG0SclFJWcaO3cBtmNP6sJ4y"
BASE_URL = "https://paper-api.alpaca.markets"

ALPACA_CONFIG = {
    # Put your own Alpaca key here:
    "API_KEY": "PKH7GY7YL14X86KSDS7Z",
    # Put your own Alpaca secret here:
    "API_SECRET": "2JL8alJYIzAxW7LKGG0SclFJWcaO3cBtmNP6sJ4y",
    # If you want to go live, you must change this. It is currently set for paper trading
    "ENDPOINT": "https://paper-api.alpaca.markets",
    "PAPER":True
}

class MLTrader(Strategy):
    
    parameters = {
            "symbol": "SPY",
            "quantity": 10,
            "side": "buy"
        }
    
    def initialize(self,cash_at_risk = 0.5, symbol=""): 
        # runs once when the bot is started
        self.symbol = self.parameters["symbol"]
        self.sleeptime = "24H" #how long will the bot run for
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, 
                        key_id = API_KEY,
                        secret_key = API_SECRET)
        
        
    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price, 0) #rounding to the nearest whole number
        return cash, last_price, quantity
    
    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime("%Y-%m-%d"), three_days_prior.strftime("%Y-%m-%d")
    
    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol = self.symbol,
                                 start = three_days_prior,
                                 end = today)
        news  = [event.__dict__["_raw"]["headline"] for event in news]
        sentiment_result = estimate_sentiment(news)
        if sentiment_result is None:
            return None, None
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment
    
    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        symbol = self.parameters["symbol"]
        probability, sentiment = self.get_sentiment()
        
        if cash>last_price:
            if sentiment == "positive" and probability>0.999:
                if self.last_trade == "sell":
                    self.sell_all()
                # print(probability, sentiment)
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy",
                    type = "bracket",
                    take_profit_price = last_price*1.20,
                    stop_loss_price = last_price*0.95
                )
                self.submit_order(order)
                self.last_trade = "buy"
            
            elif sentiment == "negative" and probability>0.999:
                if self.last_trade == "buy":
                    self.sell_all()
                # print(probability, sentiment)
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "sell",
                    type = "bracket",
                    take_profit_price = last_price*0.8,
                    stop_loss_price = last_price*1.095
                )
                self.submit_order(order)
                self.last_trade = "sell"

trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
# set up the trader
strategy = MLTrader(name='mlstrat',
                  broker=broker,
                  parameters={
                      "symbol": "SPY",
                      "cash_at_risk" : 0.5
                      }
                  ) 

# Backtest this strategy
backtesting_start = datetime(2023, 1, 1)
backtesting_end = datetime(2023, 12, 31)
strategy.backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end,
    # You can also pass in parameters to the backtesting class, this will override the parameters in the strategy
    parameters= {
        "symbol": "SPY",
        "cash_at_risk" : 0.5
    },
)

# Run the strategy live
trader.add_strategy(strategy)
trader.run_all()
