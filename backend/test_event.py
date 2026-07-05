import json
from app.services.event_service import EventService, AlertService, AlertRuleEngine
from app.models.user import User
from app.models.stock import StockState
from app.database import SessionLocal

db = SessionLocal()

try:
    # 创建测试用户（若已存在会报错，可用 merge 或先查询）
    # 为了测试，可先尝试删除再添加，或使用 db.merge
    # 简单起见，使用 add 并捕获异常
    user = User(id='u1', username='testuser')
    db.merge(user)  # 如果存在则更新，不存在则插入
    db.commit()

    # 创建事件
    esvc = EventService(db)
    e1 = esvc.create_event('600519', 'news', '茅台Q3财报超预期', impact_score=0.8)
    e2 = esvc.create_event('600519', 'price', '股价突破2000元', impact_score=0.9)
    e3 = esvc.create_event('000001', 'news', '平安银行分红', impact_score=0.3)
    print(f'全部事件: {len(esvc.get_events())} 条')
    print(f'茅台事件: {len(esvc.get_events("600519"))} 条')

    # 创建告警
    asvc = AlertService(db)
    asvc.create_alert('u1', '600519', 'score_change', '评分上升 0.6')
    asvc.create_alert('u1', '600519', 'risk_level', '风险等级升高')
    print(f'未读告警: {asvc.unread_count("u1")} 条')

    # 标记已读
    alerts = asvc.get_alerts('u1')
    if alerts:
        asvc.mark_read(alerts[0].id)
        print(f'标记后未读: {asvc.unread_count("u1")} 条')
    else:
        print('无告警可标记已读')

    # 规则引擎
    state = StockState(stock_code='600519', score=8.0, alert_level='HIGH')
    triggered = AlertRuleEngine.evaluate('600519', state, {'score': 7.0})
    print(f'规则触发: {len(triggered)} 条告警')
    for a in triggered:
        print(f'  {a["alert_type"]}: {a["message"]}')

except Exception as e:
    db.rollback()
    print(f'❌ 发生错误: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()