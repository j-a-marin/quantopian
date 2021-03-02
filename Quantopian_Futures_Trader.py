Quantopian_Futures_Trader.py

import numpy as np
import pandas as pd
from collections import OrderedDict 

# TAILORED TO QUANTOPIAN

def initialize(context):
    
    context.futures_info = {
 'Crude Oil E-Mini': {'exchange_traded': 'NYMEX',
  'min_tick': '.01',
  'tick_value': '5.00',
  'ticker_symbol': 'QM'},
 'Ethanol': {'exchange_traded': 'CBOT',
  'min_tick': '0.25',
  'tick_value': '12.50',
  'ticker_symbol': 'ET'},
 'Gold': {'exchange_traded': 'COMEX',
  'min_tick': '.10',
  'tick_value': '10.00',
  'ticker_symbol': 'GC'},
 'NASDAQ 100 E-Mini': {'exchange_traded': 'CME',
  'min_tick': '0.25',
  'tick_value': '5.00',
  'ticker_symbol': 'NQ'},
 'Natural Gas': {'exchange_traded': 'NYMEX',
  'min_tick': '.10',
  'tick_value': '10.00',
  'ticker_symbol': 'NG'},
 'S&P 500 E-Mini': {'exchange_traded': 'CME',
  'min_tick': '0.25',
  'tick_value': '12.50',
  'ticker_symbol': 'ES'}}
    
    context.futures_info = OrderedDict(sorted(context.futures_info.items(), key=lambda t: t[0]))
    # context.contract = None # Accessible across functions
    context.current_monthly_longs = {}
    context.current_monthly_shorts = {}
    context.current_monthly_neutrals = {}
    
    schedule_function(func=rebalance_monthly, 
                      date_rule=date_rules.every_day(), 
                      time_rule=time_rules.market_open(minutes=55))
    
    schedule_function(func=end_of_day, 
                      date_rule=date_rules.every_day(), 
                      time_rule=time_rules.market_close())

def rebalance_monthly(context, data):
       
    for f in context.futures_info.keys():
        # get the ticker
        ticker = context.futures_info[f]['ticker_symbol']
        # get the continuous version of it to be checked and passed along
        cf = continuous_future(ticker, offset=0, roll='volume', adjustment='mul')
        current_contract = data.current(cf, 'contract') # getting the future chain
        current_price = data.current(cf, 'price') # using actual price information for accuracy
        position, history = decision_info(context, data, cf)
        # !!! LONG SIGNAL
        ###
        # Case where we get long signal and the future is currently short or neutral
        ###
        if position == "long" and f not in context.current_monthly_longs.keys():
            
            k = amount_of_k(context, data, f, cf, current_price, 'long')
                        
                # get information from current position dictionary
                # if context.current_monthly_shorts[f]['date_short']:
                #     date_short = context.current_monthly_shorts[f]['date_short']
                
            if f in context.current_monthly_shorts.keys():
                
                context.current_monthly_longs[f] = {
                    'position': context.current_monthly_shorts[f]['position'].append(position),
                    'date_long':context.current_monthly_shorts[f]['date_long'].append(get_datetime()),
                    'date_short': context.current_monthly_shorts[f]['date_short'],
                    'k':context.current_monthly_shorts[f]['k'].append(k),
                    'stopped_out':context.current_monthly_shorts[f]['stopped_out']}
                
                del context.current_monthly_shorts[f]
                
            elif f in context.current_monthly_neutrals.keys():
                
                context.current_monthly_longs[f] = {
                    'position': context.current_monthly_neutrals[f]['position'].append(position),
                    'date_long':context.current_monthly_neutrals[f]['date_long'].append(get_datetime()),
                    'date_short': context.current_monthly_neutrals[f]['date_short'],
                    'k':context.current_monthly_neutrals[f]['k'].append(k),
                    'stopped_out':context.current_monthly_neutrals[f]['stopped_out']}
                
                del context.current_monthly_neutrals[f]
                               
            else:
                # create new dictionary for virgin long position
                context.current_monthly_longs[f] = {
                    'position': [position],
                    'date_long':[get_datetime()],
                     'date_short':[],
                    'k':[k],
                    'stopped_out':[]}
         
        ###
        # Case where we get long signal and the future is already long
        ###
        elif position == "long" and f in context.current_monthly_longs.keys():
            
            k = amount_of_k(context, data, f, cf, current_price, 'long')
            
            context.current_monthly_longs[f] = {
                'position': context.current_monthly_longs[f]['position'].append(position),
                'date_long':context.current_monthly_longs[f]['date_long'].append(get_datetime()),
                'date_short': context.current_monthly_longs[f]['date_short'],
                'k':context.current_monthly_longs[f]['k'].append(k),
                'stopped_out':context.current_monthly_longs[f]['stopped_out']}
            
        # !!! SHORT SIGNAL
        ###
        # Case where we get short signal and the future is currently long or neutral
        ###  
        elif position == "short" and f not in context.current_monthly_shorts.keys():
            
            k = amount_of_k(context, data, f, cf, current_price, 'short')
            
                # get information from current position dictionary
                # if context.current_monthly_shorts[f]['date_short']:
                #     date_short = context.current_monthly_shorts[f]['date_short']
              
            if f in context.current_monthly_longs.keys():
                
                context.current_monthly_shorts[f] = {
                    'position': context.current_monthly_longs[f]['position'].append(position),
                    'date_long':context.current_monthly_longs[f]['date_long'],
                    'date_short': context.current_monthly_longs[f]['date_short'].append(get_datetime()),
                    'k':context.current_monthly_longs[f]['k'].append(k),
                    'stopped_out':context.current_monthly_longs[f]['stopped_out']}
                
                del context.current_monthly_longs[f]
                
            elif f in context.current_monthly_neutrals.keys():
                
                context.current_monthly_shorts[f] = {
                    'position': context.current_monthly_neutrals[f]['position'].append(position),
                    'date_long':context.current_monthly_neutrals[f]['date_long'],
                    'date_short': context.current_monthly_neutrals[f]['date_short'].append(get_datetime()),
                    'k':context.current_monthly_neutrals[f]['k'].append(k),
                    'stopped_out':context.current_monthly_neutrals[f]['stopped_out']}
                
                del context.current_monthly_neutrals[f]
                    
            else:
                # create new dictionary for virgin long position
                context.current_monthly_shorts[f] = {
                    'position': [position],
                    'date_long':[],
                     'date_short':[get_datetime()],
                    'k':[k],
                    'stopped_out':[]}  
        ###
        # Case where we get short signal and the future is already short
        ###        
        elif position == "short" and f in context.current_monthly_shorts:
            
            k = amount_of_k(context, data, f, cf, current_price, 'short')
            
            context.current_monthly_shorts[f] = {
                'position': context.current_monthly_shorts[f]['position'].append(position),
                'date_long':context.current_monthly_shorts[f]['date_long'],
                'date_short': context.current_monthly_shorts[f]['date_short'].append(get_datetime()),
                'k':context.current_monthly_shorts[f]['k'].append(k),
                'stopped_out':context.current_monthly_shorts[f]['stopped_out']}
            
        # !!! NEUTRAL SIGNAL
        ###
        # Case where we get short signal and the future is currently long or neutral
        ###
        elif position == "neutral" and f not in context.current_monthly_neutrals:
            
            k = amount_of_k(context, data, f, cf, current_price, 'neutral')
            
            if f in context.current_monthly_longs.keys():
                
                context.current_monthly_neutrals[f] = {
                    'position': context.current_monthly_longs[f]['position'].append(position),
                    'date_long':context.current_monthly_longs[f]['date_long'],
                    'date_short': context.current_monthly_longs[f]['date_short'],
                    'k':context.current_monthly_longs[f]['k'].append(k),
                    'stopped_out':context.current_monthly_longs[f]['stopped_out']}
                
                del context.current_monthly_longs[f]
                
            elif f in context.current_monthly_shorts.keys():
                
                context.current_monthly_neutrals[f] = {
                    'position': context.current_monthly_shorts[f]['position'].append(position),
                    'date_long':context.current_monthly_shorts[f]['date_long'],
                    'date_short': context.current_monthly_shorts[f]['date_short'],
                    'k':context.current_monthly_shorts[f]['k'].append(k),
                    'stopped_out':context.current_monthly_shorts[f]['stopped_out']}
                
                del context.current_monthly_shorts[f]

            else:
                # create new dictionary for virgin long position
                context.current_monthly_neutrals[f] = {
                    'position': [position],
                    'date_long':[],
                     'date_short':[],
                    'k':[k],
                    'stopped_out':[]}
               
        elif position == "neutral" and f in context.current_monthly_neutrals.keys():
            
            k = amount_of_k(context, data, f, cf, current_price, 'neutral')
            
            context.current_monthly_neutrals[f] = {
                'position': context.current_monthly_neutrals[f]['position'].append(position),
                'date_long':context.current_monthly_neutrals[f]['date_long'],
                'date_short': context.current_monthly_neutrals[f]['date_short'],
                'k':context.current_monthly_neutrals[f]['k'].append(k),
                'stopped_out':context.current_monthly_neutrals[f]['stopped_out']}
    

    if context.current_monthly_longs.keys():

        for f in context.current_monthly_longs.keys():
        
            ticker = context.futures_info[f]['ticker_symbol']
            # get the continuous version of it to be checked and passed along
            cf = continuous_future(ticker, offset=0, roll='volume', adjustment='mul')
            current_contract = data.current(cf, 'contract')
            # current_price = data.current(cf, 'price')
            # k = amount_of_k(context, data, f, cf, current_price, 'long')
            k = context.current_monthly_longs[f]['k'][-1] 
            order(current_contract, k) 
        
    if context.current_monthly_shorts.keys():
        for f in context.current_monthly_shorts.keys():
            
            ticker = context.futures_info[f]['ticker_symbol']
            # get the continuous version of it to be checked and passed along
            cf = continuous_future(ticker, offset=0, roll='volume', adjustment='mul')
            current_contract = data.current(cf, 'contract')
            # current_price = data.current(cf, 'price')
            # k = amount_of_k(context, data, f, cf, current_price, 'long')
            k = context.current_monthly_shorts[f]['k'][-1] 
            order(current_contract, k) 
        
    if context.current_monthly_shorts.keys():
        for f in context.current_monthly_neutrals.keys():
            
            ticker = context.futures_info[f]['ticker_symbol']
            # get the continuous version of it to be checked and passed along
            cf = continuous_future(ticker, offset=0, roll='calendar', adjustment='mul')
            current_contract = data.current(cf, 'contract')
            # current_price = data.current(cf, 'price')
            # k = amount_of_k(context, data, f, cf, current_price, 'long')
            # k = context.current_monthly_neutrals[f]['k'][-1] 
            order_target(current_contract, 0) 
        
def amount_of_k(context, data, f, cf, current_price, direction):
    
    if direction == "long":
        k = 5
    elif direction == 'short':
        k = -5
    else:
        k = 0
    # position, history = decision_info(context, data, cf)
    # prior_close = history['close'][-2]
    # current_bar_low = history['low'][-1]
    # current_bar_high = history['high'][-1]

    # if direction == "long":
    #     min_tick = float(context.futures_info[f]['min_tick'])
    #     tick_value = float(context.futures_info[f]['tick_value'])
        
    #     num = 0.01 * context.portfolio.portfolio_value 
    #     denom = tick_value * np.true_divide( (prior_close - current_bar_low), min_tick)
    #     denom = denom * current_price
    #     k = np.floor(np.true_divide(num, denom))
    #     # k = np.floor(min(k,20))
        
    # elif direction == "short":
    #     min_tick = float(context.futures_info[f]['min_tick'])
    #     tick_value = float(context.futures_info[f]['tick_value'])
    #     num = 0.01 * context.portfolio.portfolio_value
    #     denom = tick_value * np.true_divide( (current_bar_high - prior_close), min_tick)
    #     denom = denom * current_price
    #     k = np.floor(np.true_divide(num, denom))
    #     # k = -np.floor((0.01 * context.portfolio.portfolio_value) / (np.floor((current_bar_high - prior_close) / min_tick) * tick_value))
        
    #     # k = np.floor(max(k,-20))
    # elif direction == "neutral":
    #     k = 0 
        
    return k

def decision_info(context, data, cf):
    position = 'neutral'
    # history_available = True
    # get 7 months of past data - need continuous futures for this
    df = data.history(
        assets=cf, 
        fields=['open', 'high', 'low', 'close'], 
        bar_count=142, 
        frequency='1d') 
    try:
        history = df.resample('M', base=1).first()
        history['open'] = df['open'].resample('M', base=1).first()
        history['high'] = df['high'].resample('M', base=1).max()
        history['low'] = df['low'].resample('M', base=1).min()
        history['close'] = df['close'].resample('M', base=1).last()
    except:
        return position, "no history"
    
    if np.any(np.isnan(
            [history['open'],
             history['high'],
             history['low'],
             history['close'] ] ) ):
        return position, "no history"
    else:          
        monthly_long = (data.current(cf,'price') > history['close'][-2]) and (history['low'][-1] < history['low'][-2])
    
        monthly_short = (data.current(cf,'price') < history['close'][-2]) and (history['high'][-1] > history['high'][-2])
    
        monthly_gap_up = (history['low'][-1] > history['high'][-2])
    
        monthly_gap_down = (history['high'][-1] < history['low'][-2])
    
        if monthly_long or monthly_gap_up:
            position = "long"
            return (position, history)
        elif monthly_short or monthly_gap_down:
            position = "short"
            return (position, history)
        else:
            position = "neutral"
            return (position, history)
    
def end_of_day(context, data):
    log.info(context.current_monthly_longs)
    log.info(context.current_monthly_shorts)
    log.info(context.current_monthly_neutrals)