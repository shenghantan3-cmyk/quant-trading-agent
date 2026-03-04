"""模拟账户系统"""
from typing import Dict, List, Any
from datetime import datetime
import json

class Portfolio:
    """模拟投资组合"""
    
    def __init__(self, initial_capital: float = 100000.0):
        """初始化账户"""
        self.initial_capital = initial_capital
        self.total_balance = initial_capital
        self.available = initial_capital
        self.positions = {}  # {code: {shares: 100, cost: 50.0, current_price: 52.0}}
        self.history = []  # 交易历史
        self.daily_profit = 0
        self.update_time = datetime.now()
    
    def buy(self, code: str, shares: int, price: float) -> Dict[str, Any]:
        """买入股票"""
        cost = shares * price
        
        if cost > self.available:
            return {"status": "failed", "error": "余额不足"}
        
        # 更新头寸
        if code in self.positions:
            self.positions[code]["shares"] += shares
            self.positions[code]["cost"] = (
                (self.positions[code]["cost"] * (self.positions[code]["shares"] - shares) + cost) /
                self.positions[code]["shares"]
            )
        else:
            self.positions[code] = {
                "shares": shares,
                "cost": price,
                "current_price": price
            }
        
        # 更新余额
        self.available -= cost
        self.total_balance -= cost
        
        # 记录交易
        trade = {
            "type": "BUY",
            "code": code,
            "shares": shares,
            "price": price,
            "amount": cost,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(trade)
        
        return {"status": "success", "trade": trade}
    
    def sell(self, code: str, shares: int, price: float) -> Dict[str, Any]:
        """卖出股票"""
        if code not in self.positions or self.positions[code]["shares"] < shares:
            return {"status": "failed", "error": "持仓不足"}
        
        revenue = shares * price
        cost = self.positions[code]["cost"] * shares
        profit = revenue - cost
        
        # 更新头寸
        self.positions[code]["shares"] -= shares
        if self.positions[code]["shares"] == 0:
            del self.positions[code]
        
        # 更新余额
        self.available += revenue
        self.total_balance += profit
        self.daily_profit += profit
        
        # 记录交易
        trade = {
            "type": "SELL",
            "code": code,
            "shares": shares,
            "price": price,
            "amount": revenue,
            "profit": profit,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(trade)
        
        return {"status": "success", "trade": trade}
    
    def update_prices(self, prices: Dict[str, float]):
        """更新股票价格"""
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code]["current_price"] = price
    
    def get_portfolio_value(self) -> Dict[str, Any]:
        """计算组合总价值"""
        position_value = sum(
            p["shares"] * p["current_price"]
            for p in self.positions.values()
        )
        
        total = self.available + position_value
        profit = total - self.initial_capital
        return_rate = (profit / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        return {
            "total_balance": round(total, 2),
            "available": round(self.available, 2),
            "position_value": round(position_value, 2),
            "daily_profit": round(self.daily_profit, 2),
            "total_profit": round(profit, 2),
            "return_rate": round(return_rate, 2),
            "position_count": len(self.positions)
        }
    
    def get_positions(self) -> Dict[str, Any]:
        """获取当前持仓"""
        details = []
        for code, pos in self.positions.items():
            profit = (pos["current_price"] - pos["cost"]) * pos["shares"]
            return_rate = ((pos["current_price"] - pos["cost"]) / pos["cost"] * 100) if pos["cost"] > 0 else 0
            
            details.append({
                "code": code,
                "shares": pos["shares"],
                "cost_price": round(pos["cost"], 2),
                "current_price": round(pos["current_price"], 2),
                "position_value": round(pos["shares"] * pos["current_price"], 2),
                "profit": round(profit, 2),
                "return_rate": round(return_rate, 2)
            })
        
        return details
