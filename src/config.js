// 与旧前端 CONFIG 保持一致的业务常量（app/static/js/config.js 的 Vue3 移植）

export const DATA_SOURCE_OPTIONS = {
  case: '快响信息',
  engineering: '工程文件',
  manual: '手册',
  faults: '故障报告',
}

export const DEFAULT_VISIBLE_COLUMNS = {
  case: ['申请时间', '问题描述', '答复详情', '机号/MSN', '运营人'],
  engineering: ['发布时间', '文件名称', '原因和说明', '数据类型', 'MSN有效性'],
  manual: ['申请时间', '问题描述', '答复详情', '飞机序列号/注册号/运营人'],
  faults: ['日期', '问题描述', '排故措施', '运营人', '飞机序列号', '机号'],
}

export const SEARCHABLE_COLUMNS = {
  case: ['标题', '问题描述', '答复详情', '客户期望'],
  engineering: ['文件名称', '原因和说明', '原文文本'],
  manual: ['标题', '问题描述', '答复详情', '客户期望'],
  faults: ['问题描述', '排故措施'],
}

export const DEFAULT_SEARCH_COLUMN = {
  case: '问题描述',
  engineering: '原因和说明',
  manual: '问题描述',
  faults: '问题描述',
}

export const AIRCRAFT_TYPE_OPTIONS = ['ARJ21', 'C919', '无']

export const DEFAULT_AIRCRAFT_TYPES = ['ARJ21', '无']

export const SENSITIVE_CATEGORIES = [
  'registration_numbers',
  'organizations',
  'aircraft',
  'locations',
  'other',
]

export const CATEGORY_LABELS = {
  registration_numbers: '机号/MSN',
  organizations: '组织机构',
  aircraft: '设备型号',
  locations: '地点',
  other: '其他',
}
