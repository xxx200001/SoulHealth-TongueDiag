# -*- coding: utf-8 -*-
"""
consultation_engine.py —— 模块②：双向智能问诊系统
=====================================================================
1. 被动问诊：用户主动回答症状量表（11维度0-10分）
2. 主动随访：按慢病标签 + 配置周期自动推送问卷
3. 输出：结构化症状打分，直接喂批次3证型引擎

自测：python consultation_engine.py
"""
import json
from datetime import datetime, timedelta

VERSION = "0.1.0"

# 规格书要求的固定采集维度（必须量化打分0-10）
SYMPTOM_DIMENSIONS = [
    {"key": "入睡困难", "label": "睡眠质量", "prompt": "近一周入睡困难程度", "category": "睡眠"},
    {"key": "食欲差", "label": "食欲", "prompt": "近一周食欲减退程度", "category": "消化"},
    {"key": "腹胀", "label": "腹胀", "prompt": "近一周腹胀程度", "category": "消化"},
    {"key": "便溏", "label": "大便偏稀", "prompt": "近一周大便偏稀/溏薄程度", "category": "二便"},
    {"key": "便秘", "label": "大便偏干", "prompt": "近一周排便困难程度", "category": "二便"},
    {"key": "尿黄", "label": "小便黄", "prompt": "近一周小便颜色偏深程度", "category": "二便"},
    {"key": "夜尿多", "label": "夜尿", "prompt": "近一周夜间起夜次数(0=无,10=≥5次)", "category": "二便"},
    {"key": "怕冷", "label": "怕冷", "prompt": "近一周畏寒肢冷程度", "category": "寒热"},
    {"key": "怕热", "label": "怕热", "prompt": "近一周怕热/手足心热程度", "category": "寒热"},
    {"key": "情绪抑郁", "label": "情绪低落", "prompt": "近一周情绪低落/抑郁程度", "category": "情志"},
    {"key": "烦躁易怒", "label": "烦躁易怒", "prompt": "近一周烦躁易怒程度", "category": "情志"},
    {"key": "疲劳", "label": "疲劳乏力", "prompt": "近一周疲劳乏力程度", "category": "体能"},
    {"key": "自汗", "label": "白天出汗", "prompt": "近一周白天非运动出汗程度", "category": "汗出"},
    {"key": "盗汗", "label": "夜间盗汗", "prompt": "近一周睡眠中出汗程度", "category": "汗出"},
    {"key": "刺痛固定", "label": "固定刺痛", "prompt": "近一周有无固定位置刺痛(0=无,10=剧烈)", "category": "疼痛"},
    {"key": "胀痛走窜", "label": "走窜胀痛", "prompt": "近一周有无胀痛/走窜性疼痛", "category": "疼痛"},
    {"key": "口苦", "label": "口苦", "prompt": "近一周晨起口苦程度", "category": "口味"},
    # 经期相关（仅女性）
    {"key": "经期血块", "label": "经血有块", "prompt": "近一周期经血夹块程度", "category": "经期", "sex": "F"},
    {"key": "经量少色淡", "label": "经量少色淡", "prompt": "近一周期经量偏少/色淡程度", "category": "经期", "sex": "F"},
    {"key": "经前乳胀", "label": "经前乳胀", "prompt": "经前乳房胀痛程度", "category": "经期", "sex": "F"},
]

# 随访周期配置（按慢病标签）
FOLLOWUP_SCHEDULE = {
    "default":       {"days": [7, 30]},
    "血糖异常":      {"days": [3, 7, 14, 30]},
    "肝功能异常":    {"days": [3, 7, 14]},
    "肾功能异常":    {"days": [3, 7, 14]},
    "血脂异常":      {"days": [7, 30]},
    "甲状腺异常":    {"days": [7, 14, 30]},
    "贫血":          {"days": [7, 14]},
}


class ConsultationEngine:
    """双向问诊引擎"""

    def get_questionnaire(self, sex="M", chronic_tags=None):
        """根据性别返回症状采集量表"""
        items = [d for d in SYMPTOM_DIMENSIONS
                 if "sex" not in d or d["sex"] == sex]
        return {
            "version": VERSION,
            "dimensions": items,
            "total": len(items),
            "instruction": "请对每项症状按0-10分打分，"
                           "0=完全没有，5=中等程度，10=非常严重",
        }

    def validate_answers(self, answers: dict, sex="M") -> dict:
        """校验用户提交的症状打分"""
        q = self.get_questionnaire(sex)
        valid_keys = {d["key"] for d in q["dimensions"]}
        errors, cleaned = [], {}
        for key, val in answers.items():
            if key not in valid_keys:
                continue
            try:
                v = int(val)
                if not 0 <= v <= 10:
                    errors.append(f"{key}: 分值{v}超出0-10范围")
                    continue
                cleaned[key] = v
            except (ValueError, TypeError):
                errors.append(f"{key}: 非法值{val}")
        missing = valid_keys - set(cleaned)
        return {
            "valid": not errors and not missing,
            "symptoms": cleaned,
            "missing": sorted(missing),
            "errors": errors,
        }

    def compute_risk_weight(self, current: dict, previous: dict = None) -> dict:
        """计算症状加重风险权重（当前 vs 上一次随访）"""
        if not previous:
            return {"delta": {}, "worsened": [], "improved": [],
                    "risk_flag": False}
        delta = {}
        worsened, improved = [], []
        for key in current:
            prev_val = previous.get(key, 0)
            cur_val = current[key]
            d = cur_val - prev_val
            delta[key] = d
            if d >= 3:
                worsened.append({"key": key, "delta": d,
                                 "note": f"{key}加重{d}分，下次调方自动加权修正"})
            elif d <= -3:
                improved.append({"key": key, "delta": d})
        return {
            "delta": delta,
            "worsened": worsened,
            "improved": improved,
            "risk_flag": len(worsened) >= 2,
        }

    def schedule_followup(self, chronic_tags=None, last_followup=None):
        """根据慢病标签生成下次随访时间列表"""
        now = datetime.now()
        base = last_followup or now
        tags = chronic_tags or []
        all_days = set()
        for tag in tags:
            sched = FOLLOWUP_SCHEDULE.get(tag, FOLLOWUP_SCHEDULE["default"])
            all_days.update(sched["days"])
        if not all_days:
            all_days = set(FOLLOWUP_SCHEDULE["default"]["days"])
        return {
            "scheduled": sorted([
                {"date": (base + timedelta(days=d)).strftime("%Y-%m-%d"),
                 "days_from_now": d, "tags": tags}
                for d in all_days
            ], key=lambda x: x["days_from_now"]),
            "chronic_tags": tags,
        }


# ----------------------------------------------------------------------
# 自测
# ----------------------------------------------------------------------
def _self_test():
    eng = ConsultationEngine()

    # 男性量表
    q = eng.get_questionnaire("M")
    male_keys = {d["key"] for d in q["dimensions"]}
    assert "经期血块" not in male_keys, "男性不应有经期维度"
    assert "怕冷" in male_keys

    # 女性量表
    q2 = eng.get_questionnaire("F")
    female_keys = {d["key"] for d in q2["dimensions"]}
    assert "经期血块" in female_keys

    # 校验
    answers = {d["key"]: 5 for d in q["dimensions"]}
    v = eng.validate_answers(answers, "M")
    assert v["valid"], v

    # 症状加重
    prev = {"怕冷": 3, "疲劳": 4, "便溏": 2}
    curr = {"怕冷": 8, "疲劳": 2, "便溏": 6}
    risk = eng.compute_risk_weight(curr, prev)
    assert len(risk["worsened"]) >= 1
    assert risk["risk_flag"] is True

    # 随访调度
    sched = eng.schedule_followup(["血糖异常", "肝功能异常"])
    assert len(sched["scheduled"]) >= 3

    print("=== 模块② 自测全部通过 ===")
    print(f"男性量表: {len(male_keys)} 维度")
    print(f"女性量表: {len(female_keys)} 维度")
    print(f"风险检测: 加重{len(risk['worsened'])}项, 改善{len(risk['improved'])}项")
    print(f"随访计划: {json.dumps(sched['scheduled'][:3], ensure_ascii=False)}")


if __name__ == "__main__":
    _self_test()
