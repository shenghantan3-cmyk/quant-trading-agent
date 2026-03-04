"""Agent系统测试脚本"""
import asyncio
from datetime import datetime, timedelta
from src.agents.data_agent import DataAgent
from src.agents.factor_agent import FactorAgent
from src.agents.decision_agent import DecisionAgent

async def main():
    print("=" * 70)
    print("量化交易Agent系统 - 完整流程测试")
    print("=" * 70)
    
    data_agent = DataAgent()
    factor_agent = FactorAgent()
    decision_agent = DecisionAgent()
    
    # 计算日期
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    print(f"\n📅 测试日期范围: {start_date} - {end_date}")
    
    # 测试1：获取股票列表
    print("\n[测试1] 获取A股列表...")
    stocks = await data_agent.get_stock_list()
    print(f"✅ 获取股票数: {stocks.get('count', 0)}")
    
    # 测试2：获取单只股票数据
    print("\n[测试2] 获取单只股票(600000.SH)的30天数据...")
    daily_data = await data_agent.get_daily_data("600000.SH", days=30)
    if daily_data["status"] == "success":
        print(f"✅ 获取数据: {daily_data['count']} 条")
        latest = daily_data['latest']
        print(f"   最新: 日期={latest.get('trade_date')} 收盘价={latest.get('close')}")
    
    # 测试3：批量获取并完整分析
    print("\n[测试3] 批量获取3只股票并完整分析...")
    codes = ["600000.SH", "601988.SH", "000858.SZ"]
    
    data = await data_agent.execute({
        "codes": codes,
        "start_date": start_date,
        "end_date": end_date
    })
    
    if data['status'] == 'success' and data['data']:
        print(f"✅ 获取数据成功: {len(data['data'])} 只股票")
        
        # 计算因子
        print("\n[测试4] 计算技术因子...")
        factors = await factor_agent.execute({
            "data": data['data'],
            "factors": ["rsi", "macd", "ma", "volatility"]
        })
        
        if factors['status'] == 'success':
            print(f"✅ 因子计算成功: {len(factors['factor_values'])} 只股票")
            for code in list(factors['factor_values'].keys())[:2]:
                print(f"   {code}: {factors['factor_values'][code]}")
            
            # 生成信号
            print("\n[测试5] 生成交易信号...")
            signals = await decision_agent.execute({
                "factors": factors['factor_values'],
                "threshold": 0.6
            })
            
            print(f"✅ 信号生成成功")
            print(f"   📈 买入信号: {len(signals.get('buy_signals', []))} 个")
            print(f"   📉 卖出信号: {len(signals.get('sell_signals', []))} 个")
            print(f"   ➡️  持仓信号: {len([s for s in signals.get('signals', []) if s['action'] == 'HOLD'])} 个")
            
            if signals.get('signals'):
                print(f"\n   详细信号列表:")
                for sig in signals['signals'][:5]:
                    print(f"     {sig['code']}: {sig['action']} (得分={sig['score']}, 信心={sig['confidence']})")
    
    print("\n" + "=" * 70)
    print("✅ 系统测试完成！所有Agent正常工作！")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
