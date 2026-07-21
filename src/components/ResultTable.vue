<template>
    <div class="result-panel">
        <!-- 统计信息 -->
        <div v-if="store.searchResults.length" class="stats-bar">
            <span class="total-count">共 {{ store.filteredResults.length }} 条</span>
            <div class="type-chips">
                <span
                    v-for="(count, type, idx) in store.typeStatistics"
                    :key="type"
                    class="nt-chip"
                    :class="[chipClass(idx), { 'nt-chip--dim': store.selectedType && store.selectedType !== type }]"
                    @click="store.filterByType(type)"
                >
                    {{ type }} {{ count }}
                </span>
            </div>
        </div>

        <!-- 工具栏 -->
        <div v-if="store.searchResults.length" class="toolbar">
            <el-button text size="small" :icon="Setting" @click="columnDialogVisible = true">
                列显示控制
            </el-button>
            <el-button text size="small" :icon="View" @click="store.anonymize()">
                脱敏显示
            </el-button>
            <el-button
                text
                size="small"
                :icon="Download"
                :disabled="!store.selectedRows.length"
                @click="exportCsv"
            >
                导出 CSV
            </el-button>
            <el-button
                text
                size="small"
                :icon="DataAnalysis"
                :disabled="!store.selectedRows.length"
                @click="analyzeSelected"
            >
                数据分析
            </el-button>
        </div>

        <!-- 结果表格 -->
        <el-table
            v-if="store.searchResults.length"
            ref="tableRef"
            v-loading="store.loading || store.loadingSimilarity"
            :data="store.pagedResults"
            stripe
            class="result-table"
            @selection-change="store.handleSelectionChange"
            @row-click="onRowClick"
            @sort-change="store.handleSortChange"
            :row-class-name="store.getRowClass"
        >
            <el-table-column type="selection" width="45" />
            <el-table-column prop="序号" label="序号" width="60" />
            <el-table-column
                v-for="col in store.visibleColumns"
                :key="col"
                :prop="col"
                :label="col"
                :min-width="getColumnMinWidth(col)"
                :sortable="store.dataSource === 'faults' && col === '日期' ? 'custom' : false"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <span v-html="highlightCell(scope.row[col], store.activeSearchKeywords)"></span>
                </template>
            </el-table-column>
        </el-table>

        <!-- 分页 -->
        <el-pagination
            v-if="store.searchResults.length"
            v-model:current-page="store.page"
            :page-size="store.pageSize"
            :total="store.filteredResults.length"
            layout="total, prev, pager, next"
            background
        />

        <!-- 空状态 -->
        <div v-if="!store.searchResults.length && !store.loading && !store.loadingSimilarity" class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">输入关键字或相似内容，开始搜索历史问题</div>
        </div>

        <ColumnControlDialog v-model="columnDialogVisible" />
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, View, Download, DataAnalysis } from '@element-plus/icons-vue'
import { useSearchStore } from '../stores/search'
import { highlightCell } from '../utils/highlight'
import { exportRowsToCsv } from '../utils/exportCsv'
import ColumnControlDialog from './dialogs/ColumnControlDialog.vue'

const store = useSearchStore()
const tableRef = ref(null)
const columnDialogVisible = ref(false)

const CHIP_CLASSES = ['nt-chip--blue', 'nt-chip--green', 'nt-chip--orange', 'nt-chip--purple', 'nt-chip--gray']
function chipClass(idx) {
    return CHIP_CLASSES[idx % CHIP_CLASSES.length]
}

function onRowClick(row, column, event) {
    store.handleRowClick(row, column, event, tableRef.value)
}

function exportCsv() {
    if (!store.selectedRows.length) {
        ElMessage.warning('请先选择要导出的数据')
        return
    }
    const count = exportRowsToCsv(store.selectedRows, store.visibleColumns)
    ElMessage.success(`成功导出 ${count} 条记录`)
}

function analyzeSelected() {
    if (!store.selectedRows.length) {
        ElMessage.warning('请先选择要分析的数据')
        return
    }
    if (store.selectedRows.length > 300) {
        ElMessage.warning('为确保分析页面性能，建议选择不超过300条数据')
        return
    }
    const analysisData = {
        data: store.selectedRows,
        columns: store.visibleColumns,
        dataSource: store.dataSource,
    }
    try {
        const payload = JSON.stringify(analysisData)
        localStorage.setItem('analysisData', payload)
        sessionStorage.setItem('analysisData', payload)
        window.open('/analysis', '_blank')
    } catch (error) {
        ElMessage.error('数据传递失败: ' + error.message)
    }
}

// 列宽策略：移植自旧前端 table.js 的 getColumnMinWidth
function getColumnMinWidth(column) {
    const source = store.dataSource
    if (source === 'case') {
        const widths = {
            故障发生日期: 100,
            申请时间: 100,
            问题描述: 400,
            答复详情: 400,
            相似度: 60,
            机型: 60,
            数据类型: 100,
            运营人: 60,
            ATA: 50,
            版本号: 60,
            '机号/MSN': 100,
        }
        return widths[column] || 120
    }
    if (source === 'engineering') {
        if (column === '原因和说明' || column === '原文文本') return 400
        if (column === '相似度') return 80
        if (['MSN有效性', '文件名称', '发布时间'].includes(column)) return 120
        return 100
    }
    if (source === 'faults') {
        if (column === '问题描述' || column === '排故措施') return 400
        if (column === '相似度') return 80
        return 100
    }
    if (column === '相似度') return 80
    if (column === '问题描述' || column === '答复详情') return 400
    if (['问题描述', '答复详情'].includes(column)) return 250
    return 150
}
</script>

<style scoped>
.result-panel {
    background: var(--nt-bg);
    border: 1px solid var(--nt-border-light);
    border-radius: var(--nt-radius-md);
    padding: 16px;
    min-height: 400px;
}
.stats-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.total-count {
    font-size: 13px;
    color: var(--nt-text-secondary);
}
.type-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.toolbar {
    display: flex;
    gap: 4px;
    margin-bottom: 8px;
    border-bottom: 1px solid var(--nt-border-light);
    padding-bottom: 8px;
}
.result-table {
    width: 100%;
}
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 0;
    color: var(--nt-text-tertiary);
}
.empty-icon {
    font-size: 36px;
    margin-bottom: 12px;
}
.empty-text {
    font-size: 13px;
}
</style>
