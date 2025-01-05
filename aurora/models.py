from decimal import Decimal
from enum import Enum
from typing import List, Optional

from ibapi.common import BarData
from pydantic import BaseModel


class AuroraAdviseActionEnum(Enum):
    LIMIT_BUY = 'LIMIT_BUY'
    LIMIT_SELL = 'LIMIT_SELL'
    MARKET_BUY = 'MARKET_BUY'
    MARKET_SELL = 'MARKET_SELL'
    ORDER_CANCEL = 'ORDER_CANCEL'
    HOLD = 'HOLD'


class AuroraAdvise(BaseModel):
    action: str = AuroraAdviseActionEnum.HOLD
    order_id: Optional[int] = None
    price: Decimal = 0.0
    confidence: int = 0
    reason: str = ''


class AuroraBar(BaseModel):
    date: str = ''
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0

    @staticmethod
    def to_bar(bar_data: BarData) -> 'AuroraBar':
        return AuroraBar(
            date=bar_data.date,
            open=bar_data.open,
            high=bar_data.high,
            low=bar_data.low,
            close=bar_data.close,
            volume=bar_data.volume
        )


class AuroraPosition(BaseModel):
    symbol: str = ''
    position: Decimal = 0.0
    average_cost: float = 0.0
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None


class AuroraOrder(BaseModel):
    order_id: int
    symbol: str
    quantity: int
    price: float
    type: str
    status: Optional[str] = None
    filled: Optional[Decimal] = None
    remaining: Optional[Decimal] = None
    avg_fill_price: Optional[float] = None


class AuroraDecisionConfig(BaseModel):
    sell_threshold: int = -100


class AuroraDecisionRequest(BaseModel):
    orders: List[AuroraOrder] = []
    position: Optional[AuroraPosition] = None
    one_min: str = ''
    five_min: str = ''
    thirty_min: str = ''
    config: AuroraDecisionConfig = AuroraDecisionConfig()
