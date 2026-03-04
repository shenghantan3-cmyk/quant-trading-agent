"""风控Agent - 风险评估与头寸管理"""
from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.portfolio.portfolio import Portfolio

class RiskAgent(BaseAgent):
    """风控Agent - 把控交易风险"""
    
    def __init__(self, portfolio: Portfolio = None):
        super().__init__("RiskAgent")
        self.portfolio = portfolio or Portfolio(100000.0)
        
        # 风控规则（中等）
        self.rules = {
            "max_daily_loss_ratio": -0.03,      # 单日最大亏损-3%
            "max_position_ratio": 0.10,          # 单只股票最多占10%
            "max_order_ratio": 0.05,             # 单笔订单最多占5%
            "stop_loss": -0.05,                  # 止损-5%
            "take_profit": 0.15,                 # 止盈+15%
            "max_positions": 10,                 # 最多持10只股票
            "position_correlation_threshold": 0.7  # 相关性阈值
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        风险检查与交易批准
        input: {
            "signals": [...],  # 交易信号
            "prices": {...}    # 当前价格
        }
        """
        signals = input_data.get("signals", [])
        prices = input_data.get("prices", {})
        
        if not signals:
            return {"status": "success", "approved_signals": [], "reasons": []}
        
        # 更新价格
        self.portfolio.update_prices(prices)
        
        # 获取账户状态
        portfolio_value = self.portfolio.get_portfolio_value()
        
        approved = []
        rejected = []
        reasons = []
        
        for signal in signals:
            code = signal.get("code")
            action = signal.get("action")
            
            # 检查1：日亏损限制
            if portfolio_value["daily_profit"] / portfolio_value["total_balance"] <= self.rules["max_daily_loss_ratio"]:
                rejected.append(signal)
                reasons.append(f"{code}: 今日亏损已达上限")
                continue
            
            # 检查2：头寸限制
            if action == "BUY":
                position_ratio = portfolio_value["position_value"] / portfolio_value["total_balance"]
                
                if position_ratio >= self.rules["max_position_ratio"]:
                    rejected.append(signal)
                    reasons.append(f"{code}: 头寸已满")
                    continue
                
                if len(self.portfolio.positions) >= self.rules["max_positions"]:
                    rejected.append(signal)
                    reasons.append(f"{code}: 已持有最大数量的股票")
                    continue
            
            # 检查3：已持仓的止损/止盈
            if code in self.portfolio.positions:
                pos = self.portfolio.positions[code]
                current_return = (pos["current_price"] - pos["cost"]) / pos["cost"]
                
                if current_return <= self.rules["stop_loss"]:
                    # 自动止损
                    rejected.append(signal)
                    reasons.append(f"{code}: 触发止损点 ({current_return*100:.1f}%)")
                    continue
                
                if current_return >= self.rules["take_profit"]:
                    # 自动止盈（改为SELL信号）
                    signal["action"] = "SELL"
                    signal["reason"] = "自动止盈"
                    approved.append(signal)
                    reasons.append(f"{code}: 自动止盈 ({current_return*100:.1f}%)")
                    continue
            
            # 通过所有检查
            approved.append(signal)
        
        result = {
            "status": "success",
            "approved_signals": approved,
            "rejected_signals": rejected,
            "risk_check_reasons": reasons,
            "portfolio_value": portfolio_value,
            "rules": self.rules
        }
        
        self.set_state("approved_signals", result)
        return result
    
    def check_stop_loss(self, code: str, current_price: float) -> Dict[str, Any]:
        """检查是否触发止损"""
        if code not in self.portfolio.positions:
            return {"status": "no_position"}
        
        pos = self.portfolio.positions[code]
        return_rate = (current_price - pos["cost"]) / pos["cost"]
        
        if return_rate <= self.rules["stop_loss"]:
            return {
                "status": "stop_loss_triggered",
                "code": code,
                "return_rate": round(return_rate, 4),
                "action": "SELL"
            }
        
        return {"status": "ok", "return_rate": round(return_rate, 4)}
    
    def check_take_profit(self, code: str, current_price: float) -> Dict[str, Any]:
        """检查是否触发止盈"""
        if code not in self.portfolio.positions:
            return {"status": "no_position"}
        
        pos = self.portfolio.positions[code]
        return_rate = (current_price - pos["cost"]) / pos["cost"]
        
        if return_rate >= self.rules["take_profit"]:
            return {
                "status": "take_profit_triggered",
                "code": code,
                "return_rate": round(return_rate, 4),
                "action": "SELL"
            }
        
        return {"status": "ok", "return_rate": round(return_rate, 4)}
