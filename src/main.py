"""FastAPI主应用 - 量化交易系统网关"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from src.agents.data_agent import DataAgent
from src.agents.factor_agent import FactorAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.risk_agent import RiskAgent
from src.agents.trade_agent import TradeAgent
from src.agents.enhanced_decision_agent import EnhancedDecisionAgent
from src.llm.kimi_llm import KimiLLM
from src.portfolio.portfolio import Portfolio

app = FastAPI(
    title="Quant Trading Agent System",
    description="基于LangChain的分布式多智能体量化交易平台",
    version="0.2.0"
)

# 初始化共享组件
portfolio = Portfolio(100000.0)  # 初始资金100万

# 初始化所有Agent
data_agent = DataAgent()
factor_agent = FactorAgent()
decision_agent = DecisionAgent()
enhanced_decision_agent = EnhancedDecisionAgent(use_llm=True)
risk_agent = RiskAgent(portfolio)
trade_agent = TradeAgent(portfolio)
kimi = KimiLLM()

# 请求模型
class StockRequest(BaseModel):
    codes: List[str]
    start_date: str
    end_date: str
    data_type: str = "daily"

class AnalysisRequest(BaseModel):
    codes: List[str]
    start_date: str
    end_date: str
    factors: List[str] = ["rsi", "macd", "ma"]
    threshold: float = 0.6

# ============ 基础API ============
@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Quant Trading Agent",
        "version": "0.2.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/portfolio")
async def get_portfolio():
    """查看账户状态"""
    return {
        "portfolio_value": portfolio.get_portfolio_value(),
        "positions": portfolio.get_positions(),
        "history_count": len(portfolio.history)
    }

# ============ 完整交易流程API ============
@app.post("/trading/full-pipeline")
async def full_trading_pipeline(request: AnalysisRequest):
    """
    完整交易流程：数据 -> 因子 -> 信号 -> 风控 -> 交易执行
    """
    try:
        # 第一步：获取数据
        data_result = await data_agent.execute({
            "codes": request.codes,
            "start_date": request.start_date,
            "end_date": request.end_date
        })
        
        if data_result["status"] != "success":
            raise Exception("Failed to fetch data")
        
        # 第二步：计算因子
        factor_result = await factor_agent.execute({
            "data": data_result["data"],
            "factors": request.factors
        })
        
        if factor_result["status"] != "success":
            raise Exception("Failed to calculate factors")
        
        # 第三步：生成信号
        signal_result = await decision_agent.execute({
            "factors": factor_result["factor_values"],
            "threshold": request.threshold
        })
        
        # 模拟当前价格（使用最新数据中的价格）
        prices = {}
        for item in data_result.get("data", []):
            if item.get("data"):
                latest = item["data"][0] if isinstance(item["data"], list) else {}
                prices[item["code"]] = latest.get("close", 0)
        
        # 第四步：风控检查
        risk_result = await risk_agent.execute({
            "signals": signal_result.get("signals", []),
            "prices": prices
        })
        
        # 第五步：交易执行
        trade_result = await trade_agent.execute({
            "signals": risk_result.get("approved_signals", []),
            "prices": prices
        })
        
        return {
            "status": "success",
            "pipeline": "DATA -> FACTORS -> SIGNALS -> RISK_CHECK -> TRADE_EXECUTION",
            "steps": {
                "data": {"count": len(data_result.get("data", []))},
                "factors": {"calculated": len(factor_result.get("factor_values", {}))},
                "signals": {"total": len(signal_result.get("signals", []))},
                "risk_check": {
                    "approved": len(risk_result.get("approved_signals", [])),
                    "rejected": len(risk_result.get("rejected_signals", []))
                },
                "execution": {
                    "executed": trade_result.get("executed_count", 0),
                    "failed": trade_result.get("failed_count", 0)
                }
            },
            "executed_trades": trade_result.get("executed", []),
            "portfolio_value": trade_result.get("portfolio_value"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """列出所有Agent及其功能"""
    return {
        "agents": [
            {"name": "DataAgent", "function": "获取股票实时行情数据"},
            {"name": "FactorAgent", "function": "计算技术指标因子"},
            {"name": "DecisionAgent", "function": "生成交易信号"},
            {"name": "EnhancedDecisionAgent", "function": "AI辅助的决策分析"},
            {"name": "RiskAgent", "function": "风险控制和头寸管理"},
            {"name": "TradeAgent", "function": "交易执行"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
