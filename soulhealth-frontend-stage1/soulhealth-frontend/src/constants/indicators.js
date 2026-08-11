// 规格书§三 页面2：支持的 25 类指标，分 8 组（含常用默认单位）
export const LAB_GROUPS = [
  { group: '肝功能', items: [
    { name: '谷丙转氨酶(ALT)', unit: 'U/L' },
    { name: '谷草转氨酶(AST)', unit: 'U/L' },
    { name: '谷氨酰转肽酶(GGT)', unit: 'U/L' },
    { name: '总胆红素', unit: 'μmol/L' },
    { name: '直接胆红素', unit: 'μmol/L' },
    { name: '白蛋白', unit: 'g/L' },
  ] },
  { group: '肾功能', items: [
    { name: '肌酐', unit: 'μmol/L' },
    { name: '尿素氮', unit: 'mmol/L' },
    { name: '尿酸', unit: 'μmol/L' },
  ] },
  { group: '血脂', items: [
    { name: '甘油三酯', unit: 'mmol/L' },
    { name: '总胆固醇', unit: 'mmol/L' },
    { name: '低密度脂蛋白(LDL)', unit: 'mmol/L' },
    { name: '高密度脂蛋白(HDL)', unit: 'mmol/L' },
  ] },
  { group: '血糖', items: [
    { name: '空腹血糖', unit: 'mmol/L' },
    { name: '糖化血红蛋白', unit: '%' },
  ] },
  { group: '血常规', items: [
    { name: '血红蛋白', unit: 'g/L' },
    { name: '红细胞', unit: '×10¹²/L' },
    { name: '白细胞', unit: '×10⁹/L' },
    { name: '血小板', unit: '×10⁹/L' },
    { name: '血清铁蛋白', unit: 'ng/mL' },
  ] },
  { group: '炎症', items: [
    { name: 'C反应蛋白', unit: 'mg/L' },
    { name: '血沉', unit: 'mm/h' },
  ] },
  { group: '甲状腺', items: [
    { name: '促甲状腺激素(TSH)', unit: 'mIU/L' },
  ] },
  { group: '凝血', items: [
    { name: 'D二聚体', unit: 'mg/L' },
    { name: '纤维蛋白原', unit: 'g/L' },
  ] },
]

export const ALL_INDICATORS = LAB_GROUPS.flatMap((g) =>
  g.items.map((i) => ({ ...i, group: g.group })),
)

export const GROUP_BY_NAME = Object.fromEntries(
  ALL_INDICATORS.map((i) => [i.name, i.group]),
)

// G0–G3 分级视觉（规格书§三/§五）
export const GRADES = [
  { t: 'G0 正常', c: 'var(--ok)', fg: '#fff' },
  { t: 'G1 轻度', c: 'var(--warn)', fg: '#5b4a00' },
  { t: 'G2 中度', c: 'var(--alert)', fg: '#fff' },
  { t: 'G3 重度', c: 'var(--danger)', fg: '#fff' },
]
