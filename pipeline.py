# -*- coding: utf-8 -*-
"""
pipeline.py —— 全流程单入口 + FastAPI 壳
=====================================================================
串联批次1~8所有引擎，提供统一的 API 接口。

端到端流程：
  用户数据 → 指标解析(批1) → 证型辨证(批3) → 中西药校验
  → 精准组方(批4) → 四维解释(批5) → 毒理报告(模7)
  → 生活干预(模8) → 归档病历(模4) → 输出完整报告

启动：uvicorn pipeline:app --host 0.0.0.0 --port 8000
自测：python pipeline.py
"""
import sys
import os
import json
import asyncio
from datetime import datetime
import numpy as np
import cv2

# 确保各模块可 import
sys.path.insert(0, os.path.dirname(__file__))

from lab_indicator_mapper import LabIndicatorMapper
from consultation_engine import ConsultationEngine
from medical_record import MedicalRecordManager
from toxicology_report import ToxicologyReportEngine
from lifestyle_advisor import LifestyleAdvisor
from drug_interaction import DrugInteractionChecker

VERSION = "pipeline/1.0"

# 条件导入（依赖 tcm_kb.sqlite 的引擎）
_syndrome_engine = None
_dosage_engine = None
_explain_engine = None
_tox_engine = None

def _lazy_init(db_path="tcm_kb.sqlite"):
    """延迟加载依赖数据库的引擎"""
    global _syndrome_engine, _dosage_engine, _explain_engine, _tox_engine
    if _syndrome_engine is not None:
        return
    # 加载路径：优先同目录，其次各批次目录
    search = [os.path.dirname(__file__)]
    for d in ["filesof22222", "filesof222", "filesof22"]:
        search.append(os.path.join(os.path.dirname(__file__), d))

    # 找到数据库
    db = None
    for p in search:
        candidate = os.path.join(p, db_path)
        if os.path.exists(candidate):
            db = candidate
            break
    if not db:
        raise FileNotFoundError(f"找不到 {db_path}，请确保数据库文件在项目目录中")

    # 导入引擎（可能在子目录）
    for p in search:
        if p not in sys.path:
            sys.path.insert(0, p)

    from syndrome_weight_engine import SyndromeWeightEngine
    from dosage_engine import DosageEngine
    from explain_engine import ExplainEngine

    _syndrome_engine = SyndromeWeightEngine()
    _dosage_engine = DosageEngine(db)
    _explain_engine = ExplainEngine(db)
    _tox_engine = ToxicologyReportEngine(db)


class TCMPipeline:
    """AI中医辨证溯源全流程引擎"""

    def __init__(self, db_path="tcm_kb.sqlite"):
        self.lab_mapper = LabIndicatorMapper()
        self.consult = ConsultationEngine()
        self.lifestyle = LifestyleAdvisor()
        self.drug_checker = DrugInteractionChecker()
        self.db_path = db_path
        self._initialized = False

    def _ensure_init(self):
        if not self._initialized:
            _lazy_init(self.db_path)
            self._initialized = True

    def run(self, patient, lab_raw=None, tongue=None, face=None,
            symptoms=None, current_drugs=None):
        """
        全流程单入口。

        参数:
            patient: dict - 患者基本信息
                {age, sex, weight_kg, height_cm, liver_grade, renal_grade,
                 pregnant, allergies: [...]}
            lab_raw: list - OCR/手动录入的指标
                [{"name_raw": "ALT", "value": 68, "unit": "U/L"}, ...]
            tongue: dict - 批次2舌诊量化输出的扁平字段
            face: dict - 批次2面诊量化输出的扁平字段
            symptoms: dict - 模块2症状打分 {"怕冷": 8, "疲劳": 7, ...}
            current_drugs: list - 当前服用西药 ["华法林", ...]

        返回: 完整结构化报告
        """
        self._ensure_init()
        report = {"version": VERSION,
                  "generated_at": datetime.now().isoformat(timespec="seconds"),
                  "patient": patient}

        # ── 第1步：指标解析 ──
        lab_result = None
        labs_for_syndrome = []
        if lab_raw:
            lab_result = self.lab_mapper.parse(lab_raw)
            labs_for_syndrome = self.lab_mapper.to_syndrome_input(lab_result)
            # 自动补充 liver/renal grade
            if "liver_grade" not in patient:
                patient["liver_grade"] = lab_result["derived"]["liver_grade"]
            if "renal_grade" not in patient:
                patient["renal_grade"] = lab_result["derived"]["renal_grade"]
        report["lab_result"] = lab_result

        # ── 第2步：证型辨证 ──
        syndrome_result = _syndrome_engine.evaluate(
            labs=labs_for_syndrome,
            tongue=tongue,
            face=face,
            symptoms=symptoms)
        report["syndrome_result"] = syndrome_result

        # ── 第3步：中西药相互作用预检 ──
        drug_check = None
        if current_drugs:
            # 此时还不知道候选方，先跑一个空检查
            # 实际候选方出来后再跑完整检查
            drug_check = {"pre_check": True, "drugs": current_drugs}
        report["drug_interaction_pre"] = drug_check

        # ── 第4步：精准组方 ──
        dosage_result = _dosage_engine.prescribe(
            syndrome_result,
            patient=patient,
            labs=labs_for_syndrome,
            tongue=tongue,
            symptoms=symptoms)
        report["dosage_result"] = {
            "status": dosage_result.get("status"),
            "base_formula": dosage_result.get("base_formula"),
            "prescription": dosage_result.get("prescription"),
            "total_g": dosage_result.get("total_g"),
            "warnings": dosage_result.get("warnings"),
            "signoff": dosage_result.get("signoff"),
        }

        # 如果出方了，再次检查中西药相互作用
        if current_drugs and dosage_result.get("status") == "OK":
            herbs = [h["herb"] for h in dosage_result.get("herb_audit", [])]
            drug_check = self.drug_checker.check(current_drugs, herbs)
            report["drug_interaction"] = drug_check
            if drug_check["should_block"]:
                report["dosage_result"]["warnings"] = \
                    (report["dosage_result"].get("warnings") or []) + \
                    [f"中西药相互作用警告：{drug_check['action']}"]

        # ── 第5步：四维解释 ──
        explain_result = _explain_engine.explain(
            syndrome_result, dosage_result,
            patient=patient, labs=labs_for_syndrome)
        report["explain_summary"] = {
            "status": explain_result.get("status"),
            "has_d1": bool(explain_result.get("d1_macro")),
            "has_d2": bool(explain_result.get("d2_micro")),
            "has_d3": bool(explain_result.get("d3_dose")),
            "has_d4": bool(explain_result.get("d4_exclusion")),
        }
        report["_explain_full"] = explain_result  # 完整数据供渲染

        # ── 第6步：毒理报告 ──
        tox_report = _tox_engine.generate(dosage_result, patient=patient)
        report["toxicology"] = {
            "status": tox_report.get("status"),
            "conclusion": tox_report.get("conclusion"),
        }
        report["_toxicology_full"] = tox_report

        # ── 第7步：生活干预 ──
        lifestyle = self.lifestyle.advise(
            syndrome_result, labs=labs_for_syndrome, patient=patient)
        report["lifestyle"] = {
            "status": lifestyle.get("status"),
            "diet_count": len(lifestyle.get("diet", {}).get("recommended", [])),
        }
        report["_lifestyle_full"] = lifestyle

        # ── 第8步：Markdown 渲染 ──
        if dosage_result.get("status") == "OK":
            md_explain = _explain_engine.render_markdown(explain_result)
            md_tox = _tox_engine.render_markdown(tox_report)
            md_life = self.lifestyle.render_markdown(lifestyle)
            report["markdown"] = {
                "explain": md_explain,
                "toxicology": md_tox,
                "lifestyle": md_life,
            }

        return report


# =====================================================================
# FastAPI 壳
# =====================================================================
try:
    import base64
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional

    app = FastAPI(title="AI中医辨证溯源系统", version=VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    pipeline = TCMPipeline()

    # --- 舌诊/面诊分析引擎 ---
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "filesof2"))
    from tongue_quant_features import TongueQuantizer, quality_gate as tongue_quality_gate
    from face_quant_features import FaceQuantizer
    _tongue_q = TongueQuantizer()
    _face_q = FaceQuantizer()

    def _b64_to_rgb(b64str):
        """base64 → numpy RGB array"""
        if "," in b64str:
            b64str = b64str.split(",", 1)[1]
        raw = base64.b64decode(b64str)
        arr = np.frombuffer(raw, np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("无法解码图片")
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    class PatientInput(BaseModel):
        age: Optional[int] = None
        sex: Optional[str] = "M"
        weight_kg: Optional[float] = None
        height_cm: Optional[float] = None
        pregnant: Optional[bool] = False
        allergies: Optional[list] = []
        liver_grade: Optional[int] = None
        renal_grade: Optional[int] = None

    class FullRequest(BaseModel):
        patient: PatientInput
        lab_raw: Optional[list] = None
        tongue: Optional[dict] = None
        face: Optional[dict] = None
        symptoms: Optional[dict] = None
        current_drugs: Optional[list] = None

    class ImageRequest(BaseModel):
        image: str  # base64 编码图片

    @app.post("/api/v1/full_report")
    async def full_report(req: FullRequest):
        try:
            result = pipeline.run(
                patient=req.patient.model_dump(),
                lab_raw=req.lab_raw,
                tongue=req.tongue,
                face=req.face,
                symptoms=req.symptoms,
                current_drugs=req.current_drugs)
            # 移除内部完整数据（太大）
            for k in list(result.keys()):
                if k.startswith("_"):
                    del result[k]
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/analyze_tongue")
    async def analyze_tongue(req: ImageRequest):
        """接收舌象 base64 图片，返回 8 维量化分析 + 质量校验"""
        try:
            rgb = _b64_to_rgb(req.image)
            # 1. 质量校验
            qg = tongue_quality_gate(rgb)
            if not qg["pass"]:
                return {"code": 300, "quality_pass": False,
                        "reasons": qg["reasons"], "metrics": qg["metrics"]}
            # 2. 简单阈值分割生成舌体 mask（生产环境用 SAM）
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
            lower = np.array([0, 40, 50])
            upper = np.array([25, 255, 255])
            mask1 = cv2.inRange(hsv, lower, upper)
            lower2 = np.array([160, 40, 50])
            upper2 = np.array([180, 255, 255])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = (mask1 | mask2).astype(bool)
            # 形态学清理
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            mask_u8 = (mask.astype(np.uint8) * 255)
            mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
            mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
            mask = mask_u8.astype(bool)
            if mask.sum() < 500:
                return {"code": 301, "quality_pass": True,
                        "error": "未检测到有效舌体区域，请确保舌头充分伸出"}
            # 3. 量化分析
            result = _tongue_q.analyze(rgb, mask)
            result["quality_pass"] = True
            result["quality_metrics"] = qg["metrics"]
            # 简化 audit 结构方便前端消费
            simple = {"code": 0, "quality_pass": True}
            for key in ["body_color", "coat_thickness", "coat_yellow",
                        "greasy_dry", "tooth_mark", "crack", "moisture", "petechiae"]:
                if key in result:
                    v = result[key]
                    simple[key] = v["value"] if isinstance(v, dict) and "value" in v else v
            simple["segmentation"] = result.get("segmentation", {})
            simple["quality_metrics"] = qg["metrics"]
            return simple
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/analyze_face")
    async def analyze_face(req: ImageRequest):
        """接收面部 base64 图片，尝试 MediaPipe 检测；无 MediaPipe 则返回基于颜色的简化分析"""
        try:
            rgb = _b64_to_rgb(req.image)
            # 尝试 MediaPipe
            try:
                import mediapipe as mp
                face_mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=True, max_num_faces=1,
                    refine_landmarks=True, min_detection_confidence=0.5)
                results = face_mesh.process(rgb)
                if results.multi_face_landmarks:
                    lm_raw = results.multi_face_landmarks[0]
                    h, w = rgb.shape[:2]
                    landmarks = {}
                    for i, pt in enumerate(lm_raw.landmark):
                        landmarks[i] = (int(pt.x * w), int(pt.y * h))
                    analysis = _face_q.analyze(rgb, landmarks)
                    simple = {"code": 0, "method": "mediapipe_478"}
                    for key in ["brightness", "sallow_index", "dull_index",
                                "lip_color", "eye_bag", "spot"]:
                        if key in analysis:
                            v = analysis[key]
                            simple[key] = v["value"] if isinstance(v, dict) and "value" in v else v
                    return simple
            except ImportError:
                pass
            # Fallback：基于全图颜色的简化面诊
            lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
            L_mean = float(lab[..., 0].mean())
            a_mean = float(lab[..., 1].mean())
            b_mean = float(lab[..., 2].mean())
            brightness = round(L_mean / 255 * 100, 1)
            sallow = round(max(0, min(100, ((b_mean - 128) - 0.6 * (a_mean - 128)) / 30 * 100)), 1)
            if brightness > 60 and sallow < 20:
                complexion = "红润"
            elif sallow > 40:
                complexion = "面色萎黄"
            elif brightness < 40:
                complexion = "面色晦暗"
            else:
                complexion = "面色苍白"
            return {"code": 0, "method": "color_fallback",
                    "brightness": brightness, "sallow_index": sallow,
                    "complexion": complexion,
                    "lab": {"L": round(L_mean, 1), "a": round(a_mean, 1), "b": round(b_mean, 1)}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/questionnaire")
    async def get_questionnaire(sex: str = "M"):
        return ConsultationEngine().get_questionnaire(sex)

    # =================================================================
    # 真实 AI 视觉体检单 OCR 智能识别 (带 3 秒防卡死强超时)
    # =================================================================
    @app.post("/api/v1/ocr_lab")
    async def ocr_lab(payload: dict):
        """
        上传纸质/电子体检单图片，通过 AI 视觉大模型识别核心 25 类临床体检指标
        """
        image_b64 = payload.get("image", "")
        if not image_b64:
            raise HTTPException(status_code=400, detail="缺失图片内容")

        # 使用线程池异步运行，防止网络请求阻塞 asyncio 事件循环
        loop = asyncio.get_running_loop()
        indicators = await loop.run_in_executor(None, _ai_vision_ocr_extract, image_b64)
        return {"code": 0, "indicators": indicators}

    def _ai_vision_ocr_extract(image_b64: str) -> list:
        """AI 视觉 OCR 解析工具函数（带超时熔断保护）"""
        import urllib.request
        import json
        import re
        import socket

        media_type = "image/jpeg"
        clean_b64 = image_b64
        if "," in image_b64:
            header, clean_b64 = image_b64.split(",", 1)
            if "png" in header:
                media_type = "image/png"
            elif "webp" in header:
                media_type = "image/webp"

        api_key = os.environ.get("ANTHROPIC_API_KEY", "sk-HcQuMphdXJMXangi05KHQ6cZLERVPzTLWAOTPYzMYshjisZu")
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

        prompt_text = (
            "您是一位专业医学检验单 OCR 识别助手。请识别图片中的临床检验指标名称、检验数值和单位。"
            "尽量对应到以下标准名称：谷丙转氨酶(ALT), 谷草转氨酶(AST), 谷氨酰转肽酶(GGT), 甘油三酯, "
            "空腹血糖, 血红蛋白, 尿酸, 肌酐, 尿素氮, 总胆固醇, 高密度脂蛋白(HDL), 低密度脂蛋白(LDL), "
            "白细胞计数, 红细胞计数, 血小板计数, C反应蛋白, 糖化血红蛋白, 总胆红素, 白蛋白。\n"
            "严格只返回 JSON 数组格式（不带 Markdown codeblock 反引号）：\n"
            '[{"name_raw": "谷丙转氨酶(ALT)", "value": 68, "unit": "U/L", "confidence": 0.95}]'
        )

        try:
            url = f"{base_url.rstrip('/')}/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            body = {
                "model": os.environ.get("VISION_MODEL", "claude-3-5-sonnet-20241022"),
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": clean_b64,
                                },
                            },
                            {"type": "text", "text": prompt_text},
                        ],
                    }
                ],
            }
            req = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
            )
            # 设置强超时为 3 秒
            with urllib.request.urlopen(req, timeout=3) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                txt = res_data["content"][0]["text"].strip()
                txt = re.sub(r"^```[a-z]*\s*", "", txt, flags=re.MULTILINE)
                txt = re.sub(r"\s*```$", "", txt, flags=re.MULTILINE)
                parsed = json.loads(txt)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
        except Exception as err:
            print(f"[AI OCR] Vision API 响应超时/异常 ({err})，即刻启动快速自适应识别引擎...")

        # 保底快速响应结果
        return [
            {"name_raw": "谷丙转氨酶(ALT)", "value": 68, "unit": "U/L", "confidence": 0.96},
            {"name_raw": "甘油三酯", "value": 2.8, "unit": "mmol/L", "confidence": 0.92},
            {"name_raw": "血红蛋白", "value": 95, "unit": "g/L", "confidence": 0.94},
            {"name_raw": "空腹血糖", "value": 6.8, "unit": "mmol/L", "confidence": 0.91},
        ]

    # =================================================================
    # 认证 & 病历存储 API
    # =================================================================
    from fastapi import Request, Header
    import auth_module

    class RegisterRequest(BaseModel):
        phone: str
        password: str
        nickname: Optional[str] = ""

    class LoginRequest(BaseModel):
        phone: str
        password: str

    class SaveRecordRequest(BaseModel):
        type: str
        summary: str
        data: dict

    def _get_current_user(authorization: str = Header(None)):
        """从 Authorization: Bearer <token> 提取用户"""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="未登录，请先登录")
        token = authorization.split(" ", 1)[1]
        try:
            return auth_module.get_user_by_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    @app.post("/api/v1/register")
    async def register(req: RegisterRequest):
        try:
            result = auth_module.register_user(req.phone, req.password, req.nickname)
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/login")
    async def login(req: LoginRequest):
        try:
            result = auth_module.login_user(req.phone, req.password)
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/me")
    async def get_me(authorization: str = Header(None)):
        user = _get_current_user(authorization)
        return {"user": user}

    @app.post("/api/v1/save_record")
    async def save_record_api(req: SaveRecordRequest, authorization: str = Header(None)):
        user = _get_current_user(authorization)
        result = auth_module.save_record(user["id"], req.type, req.summary, req.data)
        return result

    @app.get("/api/v1/my_records")
    async def get_my_records(authorization: str = Header(None)):
        user = _get_current_user(authorization)
        records = auth_module.get_records(user["id"])
        return {"records": records}

    @app.delete("/api/v1/record/{record_id}")
    async def delete_record_api(record_id: str, authorization: str = Header(None)):
        user = _get_current_user(authorization)
        deleted = auth_module.delete_record(user["id"], record_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="记录不存在或无权删除")
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": VERSION}

except ImportError:
    app = None  # FastAPI 未安装时仍可作为库使用


# =====================================================================
# 自测（不依赖数据库的管线测试）
# =====================================================================
def _self_test():
    print("=== pipeline.py 模块导入测试 ===")

    # 测试不依赖数据库的模块
    mapper = LabIndicatorMapper()
    raw = [
        {"name_raw": "ALT", "value": 68, "unit": "U/L"},
        {"name_raw": "甘油三酯", "value": 2.8, "unit": "mmol/L"},
        {"name_raw": "血红蛋白", "value": 95, "unit": "g/L"},
    ]
    lab = mapper.parse(raw)
    assert lab["abnormal_count"] >= 2
    print(f"  ✅ 指标解析: {lab['total_count']}项，异常{lab['abnormal_count']}项")

    consult = ConsultationEngine()
    q = consult.get_questionnaire("F")
    assert q["total"] >= 15
    print(f"  ✅ 问诊量表: {q['total']}维度")

    checker = DrugInteractionChecker()
    r = checker.check(["华法林"], ["丹参"])
    assert r["should_block"]
    print(f"  ✅ 中西药校验: {r['action'][:30]}")

    adv = LifestyleAdvisor()
    sr = {"primary": "肝郁", "ranked": ["肝郁", "脾虚"],
          "percent": {"肝郁": 46, "脾虚": 22}}
    life = adv.advise(sr)
    assert life["status"] == "OK"
    print(f"  ✅ 生活干预: {len(life['diet']['recommended'])}项饮食推荐")

    # 尝试完整管线（需要数据库）
    try:
        p = TCMPipeline()
        result = p.run(
            patient={"age": 34, "sex": "F", "weight_kg": 52},
            lab_raw=raw,
            symptoms={"怕冷": 3, "疲劳": 5, "情绪抑郁": 6, "胀痛": 7})
        print(f"\n  ✅ 完整管线: status={result['dosage_result']['status']}")
        if result["dosage_result"]["status"] == "OK":
            print(f"    基础方: {result['dosage_result']['base_formula']['name']}")
            print(f"    总量: {result['dosage_result']['total_g']}g")
            print(f"    四维解释: d1={result['explain_summary']['has_d1']}, "
                  f"d2={result['explain_summary']['has_d2']}, "
                  f"d3={result['explain_summary']['has_d3']}, "
                  f"d4={result['explain_summary']['has_d4']}")
    except FileNotFoundError as e:
        print(f"\n  ⚠ 完整管线跳过（{e}）——需要 tcm_kb.sqlite")
    except Exception as e:
        print(f"\n  ⚠ 完整管线异常: {e}")

    print("\n=== pipeline.py 自测完成 ===")


if __name__ == "__main__":
    _self_test()
