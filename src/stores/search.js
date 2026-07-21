import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import * as api from '../api/client'
import {
    AIRCRAFT_TYPE_OPTIONS,
    DATA_SOURCE_OPTIONS,
    DEFAULT_AIRCRAFT_TYPES,
    DEFAULT_SEARCH_COLUMN,
    DEFAULT_VISIBLE_COLUMNS,
    SEARCHABLE_COLUMNS,
} from '../config'

function newSearchLevel(column) {
    return { keywords: '', column_name: [column], logic: 'and', negative_filtering: false }
}

export const useSearchStore = defineStore('search', {
    state: () => ({
        dataSource: 'case',
        dataSourceOptions: DATA_SOURCE_OPTIONS,
        aircraftTypeOptions: AIRCRAFT_TYPE_OPTIONS,
        aircraftTypes: [...DEFAULT_AIRCRAFT_TYPES],

        // 列元数据
        dataSourceColumns: { case: [], engineering: [], manual: [], faults: [] },
        columns: [],
        columnVisible: {},
        searchableColumns: SEARCHABLE_COLUMNS,
        defaultSearchColumn: DEFAULT_SEARCH_COLUMN,
        defaultVisibleColumns: DEFAULT_VISIBLE_COLUMNS,

        // 搜索表单
        searchLevels: [newSearchLevel(DEFAULT_SEARCH_COLUMN.case)],
        contentSearch: { text: '', selectedColumns: [DEFAULT_SEARCH_COLUMN.case] },

        // 结果
        searchResults: [],
        total: 0,
        typeStatistics: {},
        selectedType: null,
        selectedRows: [],
        lastClickedRow: null,
        loading: false,
        loadingSimilarity: false,

        // 分页
        page: 1,
        pageSize: 50,

        // 请求序号守卫：旧响应不得覆盖新结果（修复搜索竞态）
        requestSeq: 0,

        // 敏感词
        sensitiveWords: {
            registration_numbers: [],
            organizations: [],
            aircraft: [],
            locations: [],
            other: [],
        },
    }),

    getters: {
        visibleColumns(state) {
            if (!state.columns.length) return []
            const visible = state.columns.filter(col => state.columnVisible[col])
            // 相似度列固定在最前
            if (visible.includes('相似度')) {
                return ['相似度', ...visible.filter(col => col !== '相似度')]
            }
            return visible
        },
        filteredResults(state) {
            if (!state.selectedType) return state.searchResults
            return state.searchResults.filter(item => item['数据类型'] === state.selectedType)
        },
        pagedResults() {
            const start = (this.page - 1) * this.pageSize
            return this.filteredResults.slice(start, start + this.pageSize)
        },
        // 收集所有搜索层级的关键词（去重），用于单元格高亮
        activeSearchKeywords(state) {
            const set = new Set()
            for (const level of state.searchLevels) {
                const kw = (level?.keywords || '').trim()
                if (!kw) continue
                kw.replace(/，/g, ',')
                    .split(',')
                    .map(s => s.trim())
                    .filter(Boolean)
                    .forEach(p => set.add(p))
            }
            return Array.from(set)
        },
    },

    actions: {
        // 初始化：加载列元数据，设置默认值
        async init() {
            try {
                const columnsMap = await api.fetchDataSourceColumns()
                this.dataSourceColumns = { ...this.dataSourceColumns, ...columnsMap }
            } catch (error) {
                ElMessage.error(api.errorMessage(error, '获取数据源列名失败'))
            }
            this.applyColumnsForSource()
        },

        // 根据当前数据源设置列与列可见性
        applyColumnsForSource() {
            const sourceCols = this.dataSourceColumns[this.dataSource]
            this.columns =
                sourceCols && sourceCols.length
                    ? [...sourceCols]
                    : [...(this.defaultVisibleColumns[this.dataSource] || [])]

            const defaults = this.defaultVisibleColumns[this.dataSource] || []
            const visible = {}
            this.columns.forEach(col => {
                visible[col] = defaults.includes(col)
            })
            this.columnVisible = visible

            const defaultCol = this.defaultSearchColumn[this.dataSource]
            this.searchLevels.forEach(level => {
                if (!Array.isArray(level.column_name) || !level.column_name.length) {
                    level.column_name = [defaultCol]
                }
            })
            if (!this.contentSearch.selectedColumns.length) {
                this.contentSearch.selectedColumns = [defaultCol]
            }
        },

        async setDataSource(source) {
            this.dataSource = source
            // 若该数据源列信息缺失，单独拉取一次
            if (!this.dataSourceColumns[source]?.length) {
                try {
                    const cols = await api.fetchColumns(source)
                    this.dataSourceColumns[source] = cols
                } catch (error) {
                    ElMessage.error(api.errorMessage(error, '获取数据源列名失败'))
                }
            }
            this.applyColumnsForSource()
            this.resetForm()
        },

        addLevel() {
            this.searchLevels.push(newSearchLevel(this.defaultSearchColumn[this.dataSource]))
        },

        removeLevel(index) {
            this.searchLevels.splice(index, 1)
        },

        // 搜索列多选：处理"全选"选项
        handleColumnSelectChange(selectedColumns, level) {
            const selectAllIndex = selectedColumns.indexOf('__select_all__')
            if (selectAllIndex > -1) {
                selectedColumns.splice(selectAllIndex, 1)
                const allColumns = this.dataSourceColumns[this.dataSource] || []
                const isAllSelected =
                    level.column_name.length === allColumns.length &&
                    allColumns.every(col => level.column_name.includes(col))
                level.column_name = isAllSelected ? [] : [...allColumns]
            } else {
                level.column_name = selectedColumns
            }
        },

        calculateTypeStatistics() {
            if (!this.searchResults.length) {
                this.typeStatistics = {}
                return
            }
            const stats = {}
            this.searchResults.forEach(item => {
                const type = item['数据类型'] || '未知'
                stats[type] = (stats[type] || 0) + 1
            })
            this.typeStatistics = stats
        },

        async search() {
            const hasValid = this.searchLevels.some(
                level => level.keywords?.trim() && level.column_name?.length
            )
            if (!hasValid) {
                ElMessage.warning('请输入搜索关键字并选择搜索列')
                return
            }

            const seq = ++this.requestSeq
            this.loading = true
            try {
                const result = await api.searchCases({
                    data_source: this.dataSource,
                    search_levels: this.searchLevels,
                    aircraft_types: this.aircraftTypes,
                })
                if (seq !== this.requestSeq) return // 已有更新的请求，丢弃旧响应

                this.searchResults = result.data || []
                this.total = result.total || 0
                this.selectedType = null
                this.selectedRows = []
                this.page = 1
                this.calculateTypeStatistics()
            } catch (error) {
                if (seq !== this.requestSeq) return
                ElMessage.error(api.errorMessage(error, '搜索出错'))
                this.searchResults = []
                this.total = 0
            } finally {
                if (seq === this.requestSeq) this.loading = false
            }
        },

        async similaritySearch() {
            if (!this.contentSearch.text.trim()) {
                ElMessage.warning('请输入要搜索的内容')
                return
            }
            if (!this.contentSearch.selectedColumns.length) {
                ElMessage.warning('请选择要搜索的列')
                return
            }

            const seq = ++this.requestSeq
            this.loadingSimilarity = true
            try {
                const result = await api.searchSimilarity({
                    text: this.contentSearch.text,
                    columns: this.contentSearch.selectedColumns,
                    results: this.searchResults.length ? this.searchResults : [],
                })
                if (seq !== this.requestSeq) return

                this.searchResults = result.data || []
                this.total = this.searchResults.length
                this.selectedType = null
                this.selectedRows = []
                this.page = 1

                // 有相似度列时固定显示在最前
                if (this.searchResults.length && '相似度' in this.searchResults[0]) {
                    if (!this.columns.includes('相似度')) this.columns.unshift('相似度')
                    this.columnVisible['相似度'] = true
                }

                this.calculateTypeStatistics()
                ElMessage.success('相似度搜索完成')
            } catch (error) {
                if (seq !== this.requestSeq) return
                ElMessage.error(api.errorMessage(error, '相似度搜索出错'))
                this.searchResults = []
                this.total = 0
            } finally {
                if (seq === this.requestSeq) this.loadingSimilarity = false
            }
        },

        resetForm() {
            const defaultCol = this.defaultSearchColumn[this.dataSource]
            this.searchLevels = [newSearchLevel(defaultCol)]
            this.contentSearch.text = ''
            this.searchResults = []
            this.total = 0
            this.typeStatistics = {}
            this.selectedType = null
            this.selectedRows = []
            this.lastClickedRow = null
            this.page = 1

            // 移除相似度列
            const idx = this.columns.indexOf('相似度')
            if (idx !== -1) {
                this.columns.splice(idx, 1)
                delete this.columnVisible['相似度']
            }
        },

        filterByType(type) {
            this.selectedType = this.selectedType === type ? null : type
            this.page = 1
        },

        handleSelectionChange(selection) {
            this.selectedRows = selection
        },

        // 行点击：普通点击切换选择，Shift+点击范围选择
        handleRowClick(row, column, event, tableRef) {
            if (column?.type === 'selection') return
            if (!tableRef) return

            const list = this.filteredResults
            if (event.shiftKey && this.lastClickedRow) {
                const currentIndex = list.indexOf(row)
                const lastIndex = list.indexOf(this.lastClickedRow)
                const [start, end] = [Math.min(currentIndex, lastIndex), Math.max(currentIndex, lastIndex)]
                for (let i = start; i <= end; i++) {
                    tableRef.toggleRowSelection(list[i], true)
                }
            } else {
                tableRef.toggleRowSelection(row)
            }
            this.lastClickedRow = row
        },

        getRowClass({ row }) {
            return this.selectedRows.includes(row) ? 'selected-row' : ''
        },

        // faults 数据源的日期列自定义排序
        handleSortChange({ prop, order }) {
            if (this.dataSource !== 'faults' || prop !== '日期') return
            const sorted = [...this.searchResults]
            sorted.sort((a, b) => {
                const timeA = new Date(a['日期'])
                const timeB = new Date(b['日期'])
                if (order === 'ascending') return timeA - timeB
                if (order === 'descending') return timeB - timeA
                return 0
            })
            this.searchResults = sorted
        },

        async anonymize() {
            if (!this.searchResults.length) {
                ElMessage.warning('没有可脱敏的搜索结果')
                return
            }
            let fields
            if (this.dataSource === 'engineering') {
                fields = ['原因和说明', '原文文本', '文件名称']
            } else if (this.dataSource === 'faults') {
                fields = ['问题描述', '排故措施']
            } else {
                fields = ['标题', '问题描述', '答复详情', '客户期望', '机号/MSN', '运营人']
            }
            try {
                this.searchResults = await api.anonymizeResults({
                    results: this.searchResults,
                    fields,
                    dataSource: this.dataSource,
                })
                ElMessage.success('脱敏处理完成')
            } catch (error) {
                ElMessage.error(api.errorMessage(error, '脱敏处理失败'))
            }
        },

        async loadSensitiveWords() {
            try {
                this.sensitiveWords = await api.fetchSensitiveWords()
            } catch (error) {
                ElMessage.error(api.errorMessage(error, '获取敏感词列表失败'))
            }
        },

        async addSensitiveWord(word, category) {
            try {
                await api.addSensitiveWord(word, category)
                ElMessage.success('添加成功')
                await this.loadSensitiveWords()
                return true
            } catch (error) {
                ElMessage.error(api.errorMessage(error, '添加敏感词失败'))
                return false
            }
        },

        async removeSensitiveWord(word, category) {
            try {
                await api.removeSensitiveWord(word, category)
                ElMessage.success('删除成功')
                await this.loadSensitiveWords()
            } catch (error) {
                ElMessage.error(api.errorMessage(error, '删除敏感词失败'))
            }
        },
    },
})
