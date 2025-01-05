import logging
import time
from decimal import Decimal
from typing import Dict, List

import pandas
from ibapi.client import EClient
from ibapi.common import BarData, TickerId, TickAttrib, OrderId
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.order_cancel import OrderCancel
from ibapi.order_state import OrderState
from ibapi.ticktype import TickType
from ibapi.utils import iswrapper
from ibapi.wrapper import EWrapper, logger

from aurora.agent import TradingAgent
from aurora.config import TradeBotConf
from aurora.models import AuroraDecisionRequest, AuroraPosition, AuroraBar, AuroraAdviseActionEnum, \
    AuroraOrder
from aurora.notification import DingDingMessenger
from aurora.indicators import IndicatorAnalyzer



def create_contract(instrument):
    contract = Contract()
    contract.symbol = instrument
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    return contract


class IBApi(EWrapper, EClient):
    def __init__(self, conf: TradeBotConf, agent: TradingAgent):
        EClient.__init__(self, self)
        EWrapper.__init__(self)
        # props
        self.conf = conf
        self.agent = agent
        # fields
        self.started = False
        self.nextValidOrderId = None
        self.account = None
        # messenger
        self.indicator = IndicatorAnalyzer()
        self.messenger = DingDingMessenger(conf)
        # algo data
        self.instruments = [create_contract(symbol)
                            for symbol in conf.symbols.split(',')]
        self.orders: Dict[OrderId, AuroraOrder] = {}
        self.bars: Dict[int, List[AuroraBar]] = {}
        self.positions: Dict[str, AuroraPosition] = {}

    def query(self):
        query_time = ''
        for idx, contract in enumerate(self.instruments):
            for jdx, chart in enumerate(('1 min', '5 mins', '30 mins')):
                self.reqHistoricalData(reqId=idx * 10 + jdx + 1,
                                       contract=contract,
                                       endDateTime=query_time,
                                       durationStr='1 D',
                                       barSizeSetting=chart,
                                       whatToShow='TRADES',
                                       useRTH=1,
                                       formatDate=1,
                                       keepUpToDate=False,
                                       chartOptions=[])

    def start(self):
        if self.started:
            return
        self.started = True
        self.query()

    @iswrapper
    def nextValidId(self, order_id: int):
        logging.info('setting nextValidOrderId: %d', order_id)
        self.nextValidOrderId = order_id
        if hasattr(self, 'account'):
            self.start()

    @iswrapper
    def managedAccounts(self, accounts_list: str):
        self.account = accounts_list.split(',')[0]
        self.reqAccountUpdates(True, self.account)

    @iswrapper
    def tickPrice(self, req_id: TickerId, tick_type: TickType, price: float, attrib: TickAttrib):
        logging.info(tick_type, price)

    @iswrapper
    def openOrder(self, order_id: OrderId, contract: Contract, order: Order, order_state: OrderState):
        """This function is called to feed in open orders, request by self.reqAllOpenOrders()
        """
        self.orders[order_id] = AuroraOrder(order_id=order_id,
                                            symbol=contract.symbol,
                                            quantity=order.totalQuantity,
                                            price=order.lmtPrice,
                                            type=order.orderType)

    @iswrapper
    def orderStatus(self,
                    order_id: OrderId,
                    status: str,
                    filled: Decimal,
                    remaining: Decimal,
                    avg_fill_price: float,
                    perm_id: int,
                    parent_id: int,
                    last_fill_price: float,
                    client_id: int,
                    why_held: str,
                    mkt_cap_price: float):
        """This event is called whenever the status of an order changes.
        """
        if order_id in self.orders:
            self.orders[order_id].filled = filled
            self.orders[order_id].remaining = remaining
            self.orders[order_id].avg_fill_price = avg_fill_price
            self.orders[order_id].status = status
            self.messenger.notify(
                f'order status: {self.orders[order_id].model_dump()}')

    @iswrapper
    def position(self, account: str, contract: Contract, position: Decimal, avg_cost: float):
        pos = AuroraPosition(symbol=contract.symbol,
                             position=position, average_cost=avg_cost)
        self.positions[contract.symbol] = pos

    @iswrapper
    def positionEnd(self):
        for symbol, pos in self.positions.items():
            self.execution(symbol)

    @iswrapper
    def historicalData(self, req: int, bar: BarData):
        if req in self.bars:
            last: AuroraBar = self.bars[req][-1]
            if last.date != bar.date:
                self.bars[req].append(AuroraBar.to_bar(bar))
            else:
                self.bars[req][-1] = AuroraBar.to_bar(bar)
        else:
            self.bars[req] = [AuroraBar.to_bar(bar)]

    @iswrapper
    def updatePortfolio(self,
                        contract: Contract,
                        position: Decimal,
                        market_price: float,
                        market_value: float,
                        average_cost: float,
                        unrealized_pnl: float,
                        realized_pnl: float,
                        account_name: str):
        if contract.symbol in self.positions:
            pos = self.positions[contract.symbol]
            pos.unrealized_pnl = unrealized_pnl
            pos.realized_pnl = realized_pnl

        else:
            self.positions[contract.symbol] = AuroraPosition(symbol=contract.symbol,
                                                             position=position,
                                                             average_cost=average_cost,
                                                             unrealized_pnl=unrealized_pnl,
                                                             realized_pnl=realized_pnl)
        pos = self.positions[contract.symbol]
        if pos.unrealized_pnl < -100:
            self.messenger.notify(f'position alert: {pos.model_dump()}')

    @iswrapper
    def historicalDataEnd(self, req: int, start: str, end: str):
        for k, v in self.bars.items():
            df = pandas.DataFrame(data=[bar.model_dump() for bar in v])
            df.to_csv(f'{k}.csv')
        # request positions
        self.positions.clear()
        self.reqAllOpenOrders()
        self.reqPositions()

    def execution(self, symbol: str):
        decision = AuroraDecisionRequest(
            orders=[order for order in self.orders.values()
                    if order.symbol == symbol],
            position=self.positions.get(symbol, None),
            one_min=self.indicator.analyze(self.bars.get(1, [])),
            five_min=self.indicator.analyze(self.bars.get(2, [])),
            thirty_min=self.indicator.analyze(self.bars.get(3, [])),
        )
        logging.info(decision.model_dump_json())
        advise = self.agent.ask(decision)
        if not advise:
            return
        if advise.action == AuroraAdviseActionEnum.HOLD:
            logging.info(f'Hold: {advise.reason}')
            return
        contract = create_contract(symbol)
        if advise.action == AuroraAdviseActionEnum.ORDER_CANCEL and advise.order_id:
            self.cancelOrder(orderId=advise.order_id,
                             orderCancel=OrderCancel())
            logger.info(f'cancel order: {advise.order_id}')
            self.messenger.notify(
                f'cancel order: {self.orders[advise.order_id].model_dump()}')
            del self.orders[advise.order_id]
        elif advise.action == AuroraAdviseActionEnum.LIMIT_BUY and advise.confidence >= 80:
            self.place_limit_order('BUY', advise.price, contract)
        elif advise.action == AuroraAdviseActionEnum.LIMIT_SELL and advise.confidence >= 80:
            self.place_limit_order('SELL', advise.price, contract)
        elif advise.action == AuroraAdviseActionEnum.MARKET_BUY and advise.confidence >= 80:
            self.place_market_order('BUY', contract)
        elif advise.action == AuroraAdviseActionEnum.MARKET_SELL and advise.confidence >= 80:
            self.place_market_order('SELL', contract)
        self.messenger.notify(f'place and order, action={advise.model_dump()}') 

    def place_limit_order(self, action: str, price: Decimal, contract: Contract):
        order = Order()
        order.action = action
        order.orderType = 'LMT'
        order.lmtPrice = price
        order.totalQuantity = 100
        self.placeOrder(self.next_order_id(), contract, order)

    def place_market_order(self, action: str, contract: Contract):
        order = Order()
        order.action = action
        order.orderType = 'MKT'
        order.totalQuantity = 100
        self.placeOrder(self.next_order_id(), contract, order)

    def next_order_id(self):
        if not self.nextValidOrderId:
            return 2
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    def keyboardInterrupt(self):
        self.stop()

    def stop(self):
        self.started = False
        self.reqAccountUpdates(subscribe=False, acctCode=self.account)
        logging.info('stop the whole application')

    @iswrapper
    def error(self, req: TickerId, error_code: int, error_string: str, advanced_order_reject_json=""):
        print("Error. Id:", req, "Code:", error_code, "Msg:", error_string, "AdvancedOrderRejectJson:",
              advanced_order_reject_json)
