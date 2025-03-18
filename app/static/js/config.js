// 配置相关常量
const CONFIG = {
    dataSourceOptions: {
        'case': '快响信息',
        'engineering': '工程文件',
        'manual': '手册',
        'faults': '故障报告'
    },
    // 导入对话框的数据源选项
    importDataSourceOptions: {
        'case': '快响信息',
        'engineering': '工程文件',
        'manual': '手册',
        'faults': '故障报告',
        'r_and_i_record': '部件拆换记录'
    },
    defaultVisibleColumns: {
        'case': ['申请时间', '问题描述', '答复详情', '机号/MSN', '运营人'],
        'engineering': ['发布时间', '文件名称', '原因和说明', '文件类型', 'MSN有效性'],
        'manual': ['申请时间', '问题描述', '答复详情', '飞机序列号/注册号/运营人'],
        'faults': ['日期', '问题描述', '排故措施', '运营人', '飞机序列号', '机号']
    },
    searchableColumns: {
        'case': ['标题', '问题描述', '答复详情', '客户期望'],
        'engineering': ['文件名称', '原因和说明', '原文文本'],
        'manual': ['标题', '问题描述', '答复详情', '客户期望'],
        'faults': ['问题描述', '排故措施']
    },
    defaultSearchColumn: {
        'case': '问题描述',
        'engineering': '原因和说明',
        'manual': '问题描述',
        'faults': '问题描述'
    },
    aircraftTypeOptions: ['ARJ21', 'C919', '无'],
    categoryLabels: {
        registration_numbers: '机号/MSN',
        organizations: '组织机构',
        aircraft: '设备型号',
        locations: '地点',
        other: '其他'
    }
};
