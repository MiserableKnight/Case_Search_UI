// 数据相关
const initialState = {
    searchLevels: [{
        keywords: '',
        column_name: ['问题描述'],
        logic: 'and',
        negative_filtering: false
    }],
    contentSearch: {
        text: '',
        selectedColumns: ['问题描述']
    },
    selectAll: false,
    aiInput: '',
    loading: false,
    searchResults: [],
    total: 0,
    columns: [],
    columnVisible: {},
    selectedColumns: [],
    columnDialogVisible: false,
    aiDialogVisible: false,
    aiResult: '',
    importantColumns: ['问题描述', '答复详情'],
    compactColumns: ['ATA', '版本号', '机型', '数据类型'],
    searchColumnsDialogVisible: false,
    statistics: {
        xAxis: '',
        yAxis: ''
    },
    statisticsColumns: ['机型', 'ATA', '数据类型', '申请时间'],
    defaultSearch: {
        dataSource: 'case',
        dataTypes: [],
        aircraftTypes: ["ARJ21", "无"]
    },
    defaultVisibleColumns: CONFIG.defaultVisibleColumns,
    dataSourceColumns: {
        case: [],
        engineering: [],
        manual: [],
        faults: []
    },
    dataSourceOptions: CONFIG.dataSourceOptions,
    defaultSearchColumn: CONFIG.defaultSearchColumn,
    searchableColumns: CONFIG.searchableColumns,
    availableDataTypes: [],
    dataSourceDialogVisible: false,
    selectAllDataTypes: false,
    dataTypesDialogVisible: false,
    aircraftTypesDialogVisible: false,
    selectAllAircraftTypes: false,
    tempDataSource: 'case',
    sensitiveWordDialogVisible: false,
    newWord: '',
    selectedCategory: 'organizations',
    categories: [
        'registration_numbers', 
        'organizations', 
        'aircraft', 
        'locations', 
        'other'
    ],
    activeCategory: 'organizations',
    sensitiveWords: {
        registration_numbers: [],
        organizations: [],
        aircraft: [],
        locations: [],
        other: []
    },
    typeStatistics: {},
    selectedRows: [],
    lastClickedRowIndex: null,
    lastClickedRow: null,
    importDialogVisible: false,
    importSettings: {
        dataSource: 'case',
        previewData: null,
        uploadedFile: null
    }
}; 