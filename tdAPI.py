import requests

#fill in with quote data
class Ticker:
    def __init__(self,symbol,data):
        self.symbol = symbol
        self.data = data

#fill in with options contract data #symbol is options symbol e.g. CCIV_021921P5 (hopefully guaranteed uniqueness)
class Contract:
    def __init__(self, underlying, data):
        self.symbol = underlying.symbol
        self.underlying = underlying
        self.data = data
        self.calculations = {}
        self.calculate()

    def calculate(self):
        underlying_last = float(self.underlying.data["last"])
        contract_bid = self.data["bid"] #assumes contract is not bid == 0.0, filtered out before initiating contract for now.
        if contract_bid == 0.0:
            return
        contract_days_to = self.data["daysToExpiration"]          
        contract_strike = self.data["strikePrice"]
        contract_itm = self.data["inTheMoney"] #T/F
        #assuming stock stays flat there's 2 calcs,
        #--near the money but itm, yield is contract premium + (difference in stock price)
        #--near the money but otm, yield is contract premium 
        #if the stock bumps but expires ITM, calc is same as itm 
        yield_flat = 0.0
        if contract_itm:
            yield_flat = (contract_strike - underlying_last + contract_bid)/underlying_last
        else:
            yield_flat = contract_bid / underlying_last
        yield_flat_daily = ((1+yield_flat)**(1.0/contract_days_to)) - 1
        yield_jump_called = (contract_strike - underlying_last + contract_bid)/underlying_last
        yield_jump_called_daily = ((1+yield_jump_called)**(1.0/contract_days_to)) - 1
        self.calculations = { #rounded to 5 decimals
            "yield_flat":round(yield_flat,5), 
            "yield_flat_daily":round(yield_flat_daily,5),
            "yield_jump_called":round(yield_jump_called,5),
            "yield_jump_called_daily":round(yield_jump_called_daily,5),
        }

    def csv_representation(self, columns):
        column_mapper = {
            "description": self.data["description"],
            "underlying_symbol": self.underlying.symbol,
            "underlying_last": str(self.underlying.data["last"]),
            "contract_bid": str(self.data["bid"]),
            "yield_flat": str(self.calculations["yield_flat"]),
            "yield_flat_daily": str(self.calculations["yield_flat_daily"]),
            "yield_jump_called": str(self.calculations["yield_jump_called"]),
            "yield_jump_called_daily": str(self.calculations["yield_jump_called_daily"]),
            "open_interest": str(self.data["openInterest"]),
            "delta": str(self.data["delta"]),
            "days_to_expiration": str(self.data["daysToExpiration"]),
            "is_itm": str(self.data["inTheMoney"])
        }
        cols = columns.split(",")
        return_str = ""
        for col in cols:
            return_str += column_mapper[col] + ","
        return return_str[:-1] + '\n' #remove out the last "," we added

class TDAPI:
    def __init__(self, key):
        self.consumer_key = key
        #store symbol: set<contracts>, where set<contracts> sorted in decreasing %yield/day (calc = %yield^(1/days_to_expiration))
        self.storage = {} 
    
    #returns all strikes
    def get_options(self,symbol,contract_type="CALL",include_quotes="TRUE", opt_range="ALL"): #private
        url = "https://api.tdameritrade.com/v1/marketdata/chains"
        params = {
            "apikey":self.consumer_key, 
            "symbol":symbol,
            "contractType": contract_type,
            "includeQuotes": include_quotes,
            "range":opt_range
        }
        r = requests.get(url=url, params=params)
        if r.ok:
            return r.json()
        else:
            print("[ERROR] Failed to retrieve options for symbol: " + symbol)
            return None
    
    #parse the data and add to our symbol list
    def add_symbol(self,symbol): #private
        res = self.get_options(symbol)
        if not res or res["status"] != "SUCCESS":
            print("[ERROR] no result/failed to successfully post for symbol: " + symbol)
            return None
        ticker = Ticker(symbol, res["underlying"])
        self.storage[ticker] = list()
        for putStrikes in res["callExpDateMap"]:
            for strike in res["callExpDateMap"][putStrikes]:
                for contract in res["callExpDateMap"][putStrikes][strike]:
                    if contract["bid"] == 0.0:
                        continue #no one wants it, skip it
                    coi = Contract(ticker, contract)
                    self.storage[ticker].append(coi)
        #sort by yield/day
        self.storage[ticker].sort(key=lambda x: x.calculations["yield_flat_daily"], reverse=True)
        return self.storage[ticker]
        
