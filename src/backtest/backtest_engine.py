"""回测引擎 - 历史数据策略验证"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from src.agents.data_agent import DataAgent
from src.agents.factor_agent import FactorAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.risk_agent import RiskAgent
from src.portfolio.portfolio import Portfolio

class BacktestEngine:
    """回测引擎 - 用历史数据验证量化策略"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.portfolio = Portfolio(initial_capital)
        
        # 初始化各Agent
        self.data_agent = DataAgent()
        self.factor_agent = FactorAgent()
        self.decision_agent = DecisionAgent()
        self.risk_agent = RiskAgent(self.portfolio)
        
        self.trades = []  # 交易记录
        self.daily_values = []  # 每日账户价值
        self.signals_history = []  # 信号历史
    
    async def run(self, codes: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
        """
        运行回测
        input:
            codes: 股票代码列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        """
        print(f"开始回测: {start_date} ~ {end_date}")
        print(f"初始资金: ¥{self.initial_capital:,.2f}")
        print(f"股票池: {codes}")
        print("-" * 70)
        
        try:
            # 获取历史数据
            data_result = await self.data_agent.execute({
                "codes": codes,
                "start_date": start_date,
                "end_date": end_date
            })
            
            if data_result["status"] != "success":
                return {"status": "failed", "error": "Failed to fetch data"}
            
            # 转换数据为DataFrame便于处理
            all_data = {}
            for item in data_result.get("data", []):
                code = item["code"]
                df = pd.DataFrame(item["data"])
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                df = df.sort_values('trade_date')
                all_data[code] = df
            
            # 获取交易日期（以第一只股票为基准）
            if not all_data:
                return {"status": "failed", "error": "No data available"}
            
            first_df = list(all_data.values())[0]
            trading_dates = sorted(first_df['trade_date'].unique())
            
            # 逐日回测
            for trade_date in trading_dates:
                day_data = {}
                prices = {}
                
                for code, df in all_data.items():
                    day_df = df[df['trade_date'] == trade_date]
                    if not day_df.empty:
                        day_data[code] = day_df.iloc[0].to_dict()
                        prices[code] = float(day_df.iloc[0]['close'])
                
                if not prices:
                    continue
                
                # 计算因子
                factor_data = []
                for code, row in day_data.items():
                    # 获取过去30天数据计算因子
                    df = all_data[code]
                    hist_df = df[df['trade_date'] <= trade_date].tail(30)
                    
                    if len(hist_df) >= 5:
                        factor_data.append({
                            "code": code,
                            "data": hist_df[['trade_date', 'open', 'high', 'low', 'close', 'vol']].to_dict('records')
                        })
                
                if not factor_data:
                    continue
                
                # 计算因子和信号
                factors = await self.factor_agent.execute({
                    "data": factor_data,
                    "factors": ["rsi", "macd", "ma"]
                })
                
                signals = await self.decision_agent.execute({
                    "factors": factors.get("factor_values", {}),
                    "threshold": 0.6
                })
                
                # 风控检查
                risk_result = await self.risk_agent.execute({
                    "signals": signals.get("signals", []),
                    "prices": prices
                })
                
                # 执行交易
                for signal in risk_result.get("approved_signals", []):
                    code = signal["code"]
                    action = signal["action"]
                    price = prices.get(code, 0)
                    
                    if not price:
                        continue
                    
                    # 计算交易量（按账户的5%）
                    portfolio_value = self.portfolio.get_portfolio_value()
                    trade_amount = portfolio_value["available"] * 0.05
                    shares = int(trade_amount / price)
                    
                    if shares <= 0:
                        continue
                    
                    # 执行交易
                    if action == "BUY":
                        result = self.portfolio.buy(code, shares, price)
                    elif action == "SELL":
                        result = self.portfolio.sell(code, shares, price)
                    else:
                        continue
                    
                    if result["status"] == "success":
                        self.trades.append({
                            "date": trade_date.strftime("%Y-%m-%d"),
                            "code": code,
                            "action": action,
                            "shares": shares,
                            "price": price
                        })
                
                # 记录每日账户价值
                portfolio_value = self.portfolio.get_portfolio_value()
                self.daily_values.append({
                    "date": trade_date.strftime("%Y-%m-%d"),
                    "total_value": portfolio_value["total_balance"],
                    "daily_profit": portfolio_value["daily_profit"],
                    "position_count": portfolio_value["position_count"]
                })
            
            # 计算回测统计
            stats = self._calculate_stats()
            
            return {
                "status": "success",
                "stats": stats,
                "trades": self.trades,
                "daily_values": self.daily_values[-10:],  # 最后10天
                "final_portfolio": self.portfolio.get_portfolio_value(),
                "positions": self.portfolio.get_positions()
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def _calculate_stats(self) -> Dict[str, Any]:
        """计算回测统计指标"""
        if not self.daily_values:
            return {}
        
        df = pd.DataFrame(self.daily_values)
        
        # 基础统计
        total_return = self.portfolio.total_balance - self.initial_capital
        return_rate = (total_return / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        # 风险指标
        daily_returns = df['total_value'].pct_change().dropna()
        max_drawdown = ((df['total_value'].cummax() - df['total_value']) / df['total_value'].cummax()).max() if len(df) > 0 else 0
        sharpe_ratio = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        
        # 交易统计
        buy_trades = len([t for t in self.trades if t["action"] == "BUY"])
        sell_trades = len([t for t in self.trades if t["action"] == "SELL"])
        win_trades = len([t for t in self.trades if t.get("profit", 0) > 0])
        
        return {
            "total_return": round(total_return, 2),
            "return_rate": round(return_rate, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "total_trades": len(self.trades),
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "win_trades": win_trades,
            "win_rate": round((win_trades / len(self.trades) * 100) if self.trades else 0, 2)
        }
