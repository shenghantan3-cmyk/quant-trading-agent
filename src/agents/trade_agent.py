"""交易执行Agent - 模拟下单执行"""
from typing import Dict, Any
from src.agents.base import BaseAgent
from src.portfolio.portfolio import Portfolio

class TradeAgent(BaseAgent):
    """交易执行Agent"""
    
    def __init__(self, portfolio: Portfolio = None):
        super().__init__("TradeAgent")
        self.portfolio = portfolio or Portfolio(100000.0)
        self.mode = "simulation"  # simulation or production
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行交易
        input: {
            "signals": [...],  # 经过风控审批的信号
            "prices": {...}    # 当前价格
        }
        """
        signals = input_data.get("signals", [])
        prices = input_data.get("prices", {})
        
        if not signals:
            return {"status": "success", "executed": [], "failed": []}
        
        executed = []
        failed = []
        
        for signal in signals:
            code = signal.get("code")
            action = signal.get("action")
            price = prices.get(code, 0)
            
            if not price:
                failed.append({
                    "signal": signal,
                    "error": "无法获取价格"
                })
                continue
            
            # 计算交易数量（按可用资金的5%）
            portfolio_value = self.portfolio.get_portfolio_value()
            trade_amount = portfolio_value["available"] * 0.05
            shares = int(trade_amount / price)
            
            if shares <= 0:
                failed.append({
                    "signal": signal,
                    "error": "资金不足或价格过高"
                })
                continue
            
            # 执行交易
            if action == "BUY":
                result = self.portfolio.buy(code, shares, price)
            elif action == "SELL":
                result = self.portfolio.sell(code, shares, price)
            else:
                continue
            
            if result["status"] == "success":
                executed.append({
                    "code": code,
                    "action": action,
                    "shares": shares,
                    "price": price,
                    "amount": shares * price,
                    "timestamp": result["trade"]["timestamp"]
                })
            else:
                failed.append({
                    "signal": signal,
                    "error": result.get("error")
                })
        
        result = {
            "status": "success",
            "mode": self.mode,
            "executed_count": len(executed),
            "failed_count": len(failed),
            "executed": executed,
            "failed": failed,
            "portfolio_value": self.portfolio.get_portfolio_value()
        }
        
        self.set_state("orders", result)
        return result
