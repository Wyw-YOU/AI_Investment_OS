import json
from app.services.portfolio_service import PortfolioService
from app.models.user import User
from app.models.stock import StockState
from app.database import SessionLocal

db = SessionLocal()

try:
    # 创建测试用户（注意：若用户已存在，请改为查询或使用唯一约束）
    # 如果 User 模型的 id 字段为自增整数，这里 id='u1' 可能类型不匹配
    db.add(User(id='u1', username='testuser'))
    db.commit()
    
    # 创建组合
    svc = PortfolioService(db)
    p = svc.create('u1', '我的投资组合')
    print(f'创建组合: id={p.id}, name={p.name}')
    
    # 添加候选股
    svc.add_to_pool(p.id, '600519')
    svc.add_to_pool(p.id, '000001')
    svc.add_to_pool(p.id, '601318')
    # 注意：如果 candidate_pool 是 JSON 字段，需要确保 add_to_pool 内部已序列化
    print(f'候选池: {json.loads(p.candidate_pool)}')
    
    # 添加 StockState 评分（如果 stock_code 已存在，需更新而非重复添加）
    # 为了测试，先尝试删除已存在的记录，或使用 upsert
    db.add(StockState(stock_code='600519', score=85.0, sector='白酒'))
    db.add(StockState(stock_code='000001', score=70.0, sector='银行'))
    db.add(StockState(stock_code='601318', score=65.0, sector='保险'))
    db.commit()
    
    # 权重建议
    result = svc.suggest_weights(p.id)
    print(f'权重建议: {result["weights"]}')
    print(f'权重总和: {sum(result["weights"].values()):.4f}')
    
    # 风险评分
    risk = svc.calc_risk_score(p.id)
    print(f'风险评分: {risk["risk_score"]}')
    print(f'风险等级: {risk["risk_level"]}')
    print(f'风险因素: {risk["risk_factors"]}')
    
except Exception as e:
    db.rollback()
    print(f'❌ 发生错误: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()