
import time
import sys
import os

from tdAPI import TDAPI, Ticker, Contract
from twilioAPI import TwilioAPI


key_dict = {} #api keys,tokens,etc.

class SingleUpdate:
    def __init__(self):
        self.world_set = list() #list of all contracts in the ticker_list universe
        self.grouped_world_set = dict() #ticker->list of contracts sorted

        self.td_api = TDAPI(key_dict["TD_CONSUMER_KEY"]) #not in love with the way this is routed
        self.twilio_api = TwilioAPI(key_dict["TWILIO_SID"], key_dict["TWILIO_AUTH"], key_dict["TWILIO_NUMBER"])
        
    def add_ticker_list(self, ticker_list): 
        for ticker in ticker_list:
            #really lazy rate limiter 120calls/minute, added .05s for a buffer
            time.sleep(.55)

            grouped = list()

            #ordered adds a symbol/gets the data
            result = self.td_api.add_symbol(ticker)
            if not result:
                continue
            
            for contract in result:
                self.world_set.append(contract)
                grouped.append(contract)
            
            grouped.sort(key=lambda x: x.calculations["yield_flat_daily"], reverse=True)
            self.grouped_world_set[ticker] = grouped
        
        self.world_set.sort(key=lambda x: x.calculations["yield_flat_daily"], reverse=True)

    def export_csv_grouped(self, path):
        csv_cols = "description,underlying_symbol,underlying_last,is_itm,contract_bid,days_to_expiration,yield_flat,yield_flat_daily,yield_jump_called,yield_jump_called_daily,open_interest,delta"
        grouped_fd = open(path, 'w') #make configurable
        grouped_fd.write(csv_cols+"\n")

        for ticker in self.grouped_world_set:
            contract_csv = ""
            for contract in self.grouped_world_set[ticker]:
                contract_csv += contract.csv_representation(csv_cols)
            grouped_fd.write(contract_csv)
        grouped_fd.close()
    
    def export_csv_world(self, path):
        csv_cols = "description,underlying_symbol,underlying_last,is_itm,contract_bid,days_to_expiration,yield_flat,yield_flat_daily,yield_jump_called,yield_jump_called_daily,open_interest,delta"
        world_fd = open(path, 'w') #make configurable
        world_fd.write(csv_cols+"\n")
        
        for contract in self.world_set:
            contract_csv = contract.csv_representation(csv_cols)
            world_fd.write(contract_csv)
        world_fd.close()    

    #input only Contract
    def pretty_print_contract(self, contract):
        if not isinstance(contract, Contract):
            return ""
        return f"{contract.data['description']}\nUnderlying Last: {contract.underlying.data['last']}\nYield Flat: {contract.calculations['yield_flat']}\nYield Flat Daily: {contract.calculations['yield_flat_daily']}"
        

    def send_text_world(self, number, limit=3):
        for count in range(0,min(limit,len(self.world_set))):
            message = self.pretty_print_contract(self.world_set[count])
            self.twilio_api.send_message(number, message)


if __name__ == "__main__":
    with open("keys.txt") as fd:
        for line in fd:
            entry = line.split("=")
            key_dict[entry[0].strip()] = entry[1].strip()

    ticker_list_file = "ticker_list.txt"
    if len(sys.argv) > 1:
        ticker_list_file = sys.argv[1]

    #get a consistent absolute path
    root = os.path.dirname(os.path.abspath(ticker_list_file)) + '\\'

    ticker_list = set()
    with open(ticker_list_file) as fd:
        line = fd.readline()
        num_tickers = 0
        while line:
            ticker_list.add(line.strip().upper())
            line = fd.readline()
            num_tickers+=1
    print("Working through " + ticker_list_file + " number of symbols: " + str(num_tickers))
    updater = SingleUpdate()
    updater.add_ticker_list(ticker_list)
    updater.export_csv_grouped(root + "grouped_symbol_sorted.csv")
    updater.export_csv_world(root + "world_symbol_sorted.csv")
    updater.send_text_world(key_dict["MY_PHONE_NUMBER"])