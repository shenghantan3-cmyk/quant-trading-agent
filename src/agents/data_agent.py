"""数据获取Agent - 通过tushare API获取实时行情"""
import asyncio
import pandas as pd
import tushare as ts
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.agents.base import BaseAgent
from src.config import settings

class DataAgent(BaseAgent):
    """数据获取Agent - 使用tushare API"""
    
    def __init__(self):
        super().__init__("DataAgent")
        self.pro = ts.pro_api(settings.tushare_token)
        self.cache = {}
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取股票数据
        input: {
            "codes": ["600000.SH", "600001.SH"],
            "start_date": "20240101",
            "end_date": "20240131",
            "data_type": "daily"  # daily, realtime
        }
        """
        codes = input_data.get("codes", [])
        start_date = input_data.get("start_date")
        end_date = input_data.get("end_date")
        data_type = input_data.get("data_type", "daily")
        
        if not codes:
            return {"error": "No stock codes provided", "status": "failed"}
        
        try:
            all_data = []
            
            for code in codes:
                if data_type == "daily":
                    # 获取日线数据
                    df = self.pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
                    if df is not None and not df.empty:
                        all_data.append({
                            "code": code,
                            "data": df.to_dict('records'),
                            "count": len(df)
                        })
                
                elif data_type == "realtime":
                    # 获取实时行情
                    df = self.pro.daily(ts_code=code, start_date=end_date, end_date=end_date)
                    if df is not None and not df.empty:
                        latest = df.iloc[0].to_dict()
                        all_data.append({
                            "code": code,
                            "latest": latest,
                            "price": latest.get("close", 0)
                        })
            
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "codes": codes,
                "data": all_data,
                "count": len(all_data)
            }
            
            self.set_state("latest_data", result)
            return result
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "codes": codes
            }
    
    async def get_stock_list(self) -> Dict[str, Any]:
        """获取全部A股列表"""
        try:
            df = self.pro.stock_basic(exchange='', list_status='L')
            return {
                "status": "success",
                "count": len(df),
                "stocks": df[['ts_code', 'name', 'area', 'industry']].head(20).to_dict('records')
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def get_daily_data(self, code: str, days: int = 30) -> Dict[str, Any]:
        """获取最近N天的日线数据"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            df = self.pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
            
            if df is None or df.empty:
                return {"status": "no_data", "code": code}
            
            return {
                "status": "success",
                "code": code,
                "count": len(df),
                "data": df.to_dict('records'),
                "latest": df.iloc[0].to_dict()
            }
        except Exception as e:
            return {"status": "failed", "error": str(e), "code": code}
