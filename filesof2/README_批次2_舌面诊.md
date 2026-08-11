# 批次2交付：模块③ 舌诊+面诊量化系统

交付4个文件：`tongue_quant_features.py`、`face_quant_features.py`、
`schema_module3.sql`、本说明。两个量化模块均已在离线容器跑通全部自测断言。

---

## 一、权重补货清单（共8个文件，按此下载后上传或放服务器）

03包（TonguePicture-SKaRD/TongueDiagnosis）代码齐全但权重全缺，
线上 Releases 已核实存在。全部放到 `application/net/weights/`：

| # | 文件名 | 作用 | 下载地址 |
|---|--------|------|----------|
| 1 | yolov5.pt | 舌体定位 | https://github.com/TonguePicture-SKaRD/TongueDiagnosis/releases/download/V1.0_Beta/yolov5.pt |
| 2 | sam_vit_b_01ec64.pth | SAM分割(ViT-B, Meta官方, ~360MB) | https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth |
| 3 | tongue_color.pth | 舌色5分类头(ResNet50, ~100MB级) | https://github.com/TonguePicture-SKaRD/TongueDiagnosis/releases/download/V1.0_Beta/tongue_color.pth |
| 4 | tongue_coat_color.pth | 苔色3分类头 | https://github.com/TonguePicture-SKaRD/TongueDiagnosis/releases/download/V1.0_Beta/tongue_coat_color.pth |
| 5 | thickness.pth | 厚薄2分类头 | https://github.com/TonguePicture-SKaRD/TongueDiagnosis/releases/download/V1.0_Beta/thickness.pth |
| 6 | rot_and_greasy.pth | 腐腻2分类头 | https://github.com/TonguePicture-SKaRD/TongueDiagnosis/releases/download/V1.0_Beta/rot_and_greasy.pth |
| 7 | unet.pth | 备用分割网络 | https://github.com/TonguePicture-SKaRD/TongueDiagnosis/releases/download/V1.0_Beta/unet.pth |
| 8 | face_landmarker.task | 面诊478点landmark(~3.7MB) | 官方 https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task ；国内被墙可用镜像 https://github.com/sanderdesnaijer/mediapipe-model-mirrors/releases/download/v1/face_landmarker.task |

面诊推理端另需 `pip install mediapipe`（Apache-2.0，无需训练）。
03后端环境：Python 3.9 + `pip install -r requirements.txt`，
数据库初始化用其 models/ 下4个 create_*.sql，再执行本批 `schema_module3.sql`。

## 二、⚠️ 许可证风险（商用前必须决策）

- 03项目本体 **AGPL-3.0**，其依赖的 yolov5(ultralytics) 同为 AGPL-3.0。
  以网络服务方式商用，AGPL 要求向用户提供该服务衍生代码的源码。
- SAM 是 Apache-2.0、MediaPipe 是 Apache-2.0：干净。
- 本批两个量化模块是**独立自研文件**，只消费"图像+mask/landmark"，
  不 import 03的任何代码，可随时整体迁移。
- 三条出路：A. 舌诊做成独立微服务并对该服务开源合规；
  B. 购买 Ultralytics 商业授权 + 用公开舌象数据集自训分类头替换；
  C. 分割换成 Apache 系(SAM+自训检测)。建议先按A跑通业务再决定。

## 三、集成点（改动仅3处）

`application/net/predict.py` 中 `masks = np.transpose(masks, (1,2,0))` 之后插入：

```python
from tongue_quant_features import TongueQuantizer, quality_gate
# ① 入口处（predict()收到img后）先跑 quality_gate，不合格 code=204 直接拒绝
# ② 分割后：
quant = TongueQuantizer().analyze(original_img, masks[:, :, 0])
predict_result["quant"] = quant
```

回调 `fun(...)` 增加 `quant_json=json.dumps(quant)` 一并落库到
`tongue_quant` 表；ResNet四个头的类别号写入 resnet_* 列，与量化层
分类做交叉验证（如 ResNet 判黄苔而量化层 yellow_index<30 → 置
cross_check_conflict=1，触发 user_confirmed 人审，逻辑同批次1）。

面诊为新增独立接口：MediaPipe 检 landmark（归一化坐标×宽高转像素）
→ `FaceQuantizer().analyze(img, landmarks)` → 落 `face_quant` 表。

## 四、能力边界（诚实声明）

- 8+6个量化字段的**分类阈值是v1启发式**（Lab色彩空间+形态学），全部
  标注 needs_clinical_calibration；上线前须用200+张标注舌象/面象回归
  校准阈值表（两个模块的 THRESH 字典就是为此集中设计的）。
- 舌苔"厚度"由2D单图估计，是覆盖率×透底度的代理量，已强制 needs_review。
- 关注项：2026年公开的6719张标准化舌象数据集（20类病理标注，双人核验）
  可用于日后自训裂纹/瘀点/齿痕专用头，替代启发式——第3批之后再议。

## 五、与整体需求的对位

规格书模块③要求的量化字段：舌诊8项、面诊6项——本批全部落地为可入库
数值+审计；"拍摄强制校验拦截"由 quality_gate 实现（端侧+后端双跑）；
"输出标准证型占比"属于证型权重引擎，消费本批数值，排第3批（与
04/05/06/07 组方·知识图谱一起做，数据源已在手）。
