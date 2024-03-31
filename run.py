import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread

# NOTE: for documentation on the different classes and methods used to interact with the SHIFT system, 
# see: https://github.com/hanlonlab/shift-python/wiki

def cancel_orders(trader, ticker):
    # cancel all the remaining orders
    for order in trader.get_waiting_list():
        if (order.symbol == ticker):
            trader.submit_cancellation(order)
            sleep(1)  # the order cancellation needs a little time to go through


def close_positions(trader, ticker):
    # NOTE: The following orders may not go through if:
    # 1. You do not have enough buying power to close your short postions. Your strategy should be formulated to ensure this does not happen.
    # 2. There is not enough liquidity in the market to close your entire position at once. You can avoid this either by formulating your
    #    strategy to maintain a small position, or by modifying this function to close ur positions in batches of smaller orders.

    # close all positions for given ticker
    print(f"running close positions function for {ticker}")

    item = trader.get_portfolio_item(ticker)

    # close any long positions
    long_shares = item.get_long_shares()
    if long_shares > 0:
        print(f"market selling because {ticker} long shares = {long_shares}")
        order = shift.Order(shift.Order.Type.MARKET_SELL,
                            ticker, int(long_shares/100))  # we divide by 100 because orders are placed for lots of 100 shares
        trader.submit_order(order)
        sleep(1)  # we sleep to give time for the order to process

    # close any short positions
    short_shares = item.get_short_shares()
    if short_shares > 0:
        print(f"market buying because {ticker} short shares = {short_shares}")
        order = shift.Order(shift.Order.Type.MARKET_BUY,
                            ticker, int(short_shares/100))
        trader.submit_order(order)
        sleep(1)

def get_bids_asks_medium(lst):
    prices = list(map(lambda x: x.price, lst))
    sizes = list(map(lambda x: x.size, lst))
    midpoint = sum(sizes)//2
    t=0
    for i in zip(sizes,prices):
        t+=i[0]
        if midpoint <= t:
            return i[1] 
    return 0

def get_order_book_medium(trader: shift.Trader, symbol: str):
    bids = trader.get_order_book(symbol, shift.OrderBookType.GLOBAL_BID, max_level=99)
    asks = trader.get_order_book(symbol, shift.OrderBookType.GLOBAL_ASK, max_level=99)
    bidm = get_bids_asks_medium(bids)
    askm = get_bids_asks_medium(asks)
    return((bidm,asks))


def strategy(trader: shift.Trader, ticker: str, endtime):
    # NOTE: Unlike the following sample strategy, it is highly reccomended that you track and account for your buying power and
    # position sizes throughout your algorithm to ensure both that have adequite captial to trade throughout the simulation and
    # that you are able to close your position at the end of the strategy without incurring major losses.

    initial_pl = trader.get_portfolio_item(ticker).get_realized_pl()

    # strategy parameters
    check_freq = 1
    order_size = 5  # NOTE: this is 5 lots which is 500 shares.

    # strategy variables
    previous_price = 0
    previous_ask = 0
    previous_bid = 0

    #buy wait adjust
    holding = 0
    selling = 0

    limit_buy = None

    sell_cycle = 0

    stage = 'buy'
    
    while (trader.get_last_trade_time() < endtime):
        best_price = trader.get_best_price(ticker)
        best_bid = best_price.get_bid_price()
        best_ask = best_price.get_ask_price()
        midprice = (best_bid + best_ask) / 2

        if stage == 'buy':
            # reset portfolio
            stock = trader.get_portfolio_item(ticker)
            print(
                "%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s"
                % (
                    stock.get_symbol(),
                    stock.get_shares(),
                    stock.get_price(),
                    stock.get_realized_pl(),
                    stock.get_timestamp(),
                )
            )
            order = shift.Order(
                shift.Order.Type.MARKET_SELL, ticker, stock.get_shares()//100)
            trader.submit_order(order)
            
            
            cancel_orders(trader, ticker)
            
            limit_buy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, best_ask)
            trader.submit_order(limit_buy)
            
            holding == 0
            sell_cycle = 0
            stage = 'sell'            
        elif stage == 'sell':
            print("sell:", sell_cycle)
            for order in trader.get_waiting_list():
                print(
                    "%6s\t%16s\t%7.2f\t\t%4d\t\t%4d\t%36s\t%23s\t\t%26s"
                    % (
                        order.symbol,
                        order.type,
                        order.executed_price,
                        order.size,
                        order.executed_size,
                        order.id,
                        order.status,
                        order.timestamp,
                    )
                )               
            for order in trader.get_executed_orders(limit_buy.id):
                print(
                    "%6s\t%16s\t%7.2f\t\t%4d\t\t%4d\t%36s\t%23s\t\t%26s"
                    % (
                        order.symbol,
                        order.type,
                        order.executed_price,
                        order.size,
                        order.executed_size,
                        order.id,
                        order.status,
                        order.timestamp,
                    )
                )
                c =+ order.executed_size
                if c<= holding:
                    continue
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order.executed_size, best_bid)
                trader.submit_order(order)
                
            sell_cycle += 1

            if sell_cycle>10:
                stage = 'buy'

        # cancel unfilled orders from previous time-step

        # get necessary data
        
##        best_price = trader.get_best_price(ticker)
##        best_bid = best_price.get_bid_price()
##        best_ask = best_price.get_ask_price()
##        midprice = (best_bid + best_ask) / 2
##
##        medium_ask = get_order_book_medium(trader, ticker)
##        medium_ask = medium_ask[1]
##        medium_bid = medium_ask[0]
##
##        #print("{} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f}".format(ticker, previous_ask, previous_bid, medium_ask, medium_bid, previous_price, midprice))
##        #print("{} {} {} {} {} {} {}".format(ticker, previous_ask, previous_bid, medium_ask, medium_bid, previous_price, midprice))
##
##        shift.Order.Type.MARKET_BUY, ticker, order_size)
##        
##        # place order
##        if (midprice > previous_price):  # price has increased since last timestep
##            # we predict price will continue to go up
##            order = shift.Order(
##                shift.Order.Type.MARKET_BUY, ticker, order_size)
##            trader.submit_order(order)
##        elif (midprice < previous_price):  # price has decreased since last timestep
##            # we predict price will continue to go down
##            order = shift.Order(
##                shift.Order.Type.MARKET_SELL, ticker, order_size)
##            trader.submit_order(order)


        
        sleep(check_freq)

    # cancel unfilled orders and close positions for this ticker
    cancel_orders(trader, ticker)
    close_positions(trader, ticker)

    print(
        f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - initial_pl}")


def print_current_portfolio():
    print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
    print(
            "%12.2f\t%12d\t%9.2f\t%26s"
            % (
                    trader.get_portfolio_summary().get_total_bp(),
                    trader.get_portfolio_summary().get_total_shares(),
                    trader.get_portfolio_summary().get_total_realized_pl(),
                    trader.get_portfolio_summary().get_timestamp(),
            )
    )
def print_portfolio_items():
    print("Symbol\t\tShares\t\tPrice\t\tP&L\t\tTimestamp")
    for item in trader.get_portfolio_items().values():
        print(
            "%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s"
            % (
                item.get_symbol(),
                item.get_shares(),
                item.get_price(),
                item.get_realized_pl(),
                item.get_timestamp(),
            )
        )

def main(trader):
    # keeps track of times for the simulation
    check_frequency = 60
    current = trader.get_last_trade_time()
    # start_time = datetime.combine(current, dt.time(9, 30, 0))
    # end_time = datetime.combine(current, dt.time(15, 50, 0))
    start_time = current
    end_time = start_time + timedelta(minutes=1)

    while trader.get_last_trade_time() < start_time:
        print("still waiting for market open")
        sleep(check_frequency)

    # we track our overall initial profits/losses value to see how our strategy affects it
    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    print_current_portfolio()
    print_portfolio_items()
 
    threads = []

    # in this example, we simultaneously and independantly run our trading alogirthm on two tickers
    tickers = ["AAPL"]

    print("START")

    for ticker in tickers:
        # initializes threads containing the strategy for each ticker
        threads.append(
            Thread(target=strategy, args=(trader, ticker, end_time)))

    for thread in threads:
        thread.start()
        sleep(1)

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time:
        sleep(check_frequency)

    # wait for all threads to finish
    for thread in threads:
        # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
        # setting the timeout argument for join() can prevent this
        thread.join()

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    print("END")
    print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")
    print(
        f"final profits/losses: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")


if __name__ == '__main__':
    with shift.Trader("exp_test000") as trader:
        trader.connect("initiator.cfg", "AywcIs6l")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)

        main(trader)
