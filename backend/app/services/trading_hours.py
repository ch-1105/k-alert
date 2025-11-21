"""
A股交易时间判断工具
Trading hours utilities for A-share market
"""
from datetime import datetime, time
from loguru import logger

class TradingHours:
    """A股交易时间判断"""
    
    # A股交易时间段
    MORNING_START = time(9, 30)      # 上午开盘
    MORNING_END = time(11, 30)       # 上午收盘
    AFTERNOON_START = time(13, 0)    # 下午开盘
    AFTERNOON_END = time(15, 0)      # 下午收盘
    
    # 集合竞价时间
    CALL_AUCTION_START = time(9, 15)  # 集合竞价开始
    CALL_AUCTION_END = time(9, 25)    # 集合竞价结束
    
    @staticmethod
    def is_trading_day(dt: datetime = None) -> bool:
        """
        判断是否为交易日（排除周末）
        注意：此方法不考虑节假日，仅判断是否为周一至周五
        
        Args:
            dt: 要判断的日期时间，默认为当前时间
            
        Returns:
            bool: 是否为交易日
        """
        if dt is None:
            dt = datetime.now()
        
        # 0=周一, 6=周日
        weekday = dt.weekday()
        is_weekday = weekday < 5  # 周一到周五
        
        return is_weekday
    
    @staticmethod
    def is_trading_time(dt: datetime = None, include_call_auction: bool = False) -> bool:
        """
        判断是否在交易时间内
        
        Args:
            dt: 要判断的日期时间，默认为当前时间
            include_call_auction: 是否包含集合竞价时间
            
        Returns:
            bool: 是否在交易时间内
        """
        if dt is None:
            dt = datetime.now()
        
        # 首先判断是否为交易日
        if not TradingHours.is_trading_day(dt):
            return False
        
        current_time = dt.time()
        
        # 上午交易时间段
        morning_session = (
            TradingHours.MORNING_START <= current_time <= TradingHours.MORNING_END
        )
        
        # 下午交易时间段
        afternoon_session = (
            TradingHours.AFTERNOON_START <= current_time <= TradingHours.AFTERNOON_END
        )
        
        # 集合竞价时间段（如果需要）
        call_auction = False
        if include_call_auction:
            call_auction = (
                TradingHours.CALL_AUCTION_START <= current_time <= TradingHours.CALL_AUCTION_END
            )
        
        return morning_session or afternoon_session or call_auction
    
    @staticmethod
    def get_trading_status(dt: datetime = None) -> dict:
        """
        获取当前交易状态的详细信息
        
        Args:
            dt: 要判断的日期时间，默认为当前时间
            
        Returns:
            dict: 包含交易状态的详细信息
        """
        if dt is None:
            dt = datetime.now()
        
        is_trading_day = TradingHours.is_trading_day(dt)
        is_trading_time = TradingHours.is_trading_time(dt, include_call_auction=False)
        is_call_auction = False
        
        current_time = dt.time()
        status = "closed"  # 默认状态：休市
        
        if is_trading_day:
            if TradingHours.CALL_AUCTION_START <= current_time <= TradingHours.CALL_AUCTION_END:
                status = "call_auction"
                is_call_auction = True
            elif is_trading_time:
                if TradingHours.MORNING_START <= current_time <= TradingHours.MORNING_END:
                    status = "morning_session"
                elif TradingHours.AFTERNOON_START <= current_time <= TradingHours.AFTERNOON_END:
                    status = "afternoon_session"
            elif current_time < TradingHours.CALL_AUCTION_START:
                status = "before_market"
            elif TradingHours.MORNING_END < current_time < TradingHours.AFTERNOON_START:
                status = "lunch_break"
            elif current_time > TradingHours.AFTERNOON_END:
                status = "after_market"
        else:
            # 周末
            weekday = dt.weekday()
            if weekday == 5:
                status = "weekend_saturday"
            elif weekday == 6:
                status = "weekend_sunday"
        
        return {
            "datetime": dt.isoformat(),
            "is_trading_day": is_trading_day,
            "is_trading_time": is_trading_time,
            "is_call_auction": is_call_auction,
            "status": status,
            "weekday": dt.strftime("%A"),
            "time": dt.strftime("%H:%M:%S")
        }
    
    @staticmethod
    def should_use_realtime_api(dt: datetime = None) -> bool:
        """
        判断是否应该使用实时行情API
        在交易时间内使用实时API，否则使用历史数据API
        
        Args:
            dt: 要判断的日期时间，默认为当前时间
            
        Returns:
            bool: 是否应该使用实时API
        """
        return TradingHours.is_trading_time(dt, include_call_auction=True)


# 便捷函数
def is_market_open(dt: datetime = None) -> bool:
    """
    快捷函数：判断市场是否开盘
    
    Args:
        dt: 要判断的日期时间，默认为当前时间
        
    Returns:
        bool: 市场是否开盘
    """
    return TradingHours.is_trading_time(dt, include_call_auction=False)


def get_market_status(dt: datetime = None) -> str:
    """
    快捷函数：获取市场状态描述
    
    Args:
        dt: 要判断的日期时间，默认为当前时间
        
    Returns:
        str: 市场状态描述
    """
    status_info = TradingHours.get_trading_status(dt)
    
    status_map = {
        "call_auction": "集合竞价",
        "morning_session": "上午交易",
        "afternoon_session": "下午交易",
        "lunch_break": "午间休市",
        "before_market": "盘前",
        "after_market": "盘后",
        "weekend_saturday": "周六休市",
        "weekend_sunday": "周日休市",
        "closed": "休市"
    }
    
    return status_map.get(status_info["status"], "未知状态")


if __name__ == "__main__":
    # 测试代码
    print("A股交易时间判断工具测试")
    print("=" * 50)
    
    status = TradingHours.get_trading_status()
    print(f"当前时间: {status['datetime']}")
    print(f"星期: {status['weekday']}")
    print(f"时刻: {status['time']}")
    print(f"是否交易日: {status['is_trading_day']}")
    print(f"是否交易时间: {status['is_trading_time']}")
    print(f"市场状态: {get_market_status()}")
    print(f"是否应使用实时API: {TradingHours.should_use_realtime_api()}")
