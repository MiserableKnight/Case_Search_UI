<template>
  <div class="result-section">
    <!-- 结果统计信息 -->
    <div class="result-count-container" v-if="store.searchResults.length">
      <div class="total-count">
        共找到 {{ store.searchResults.length }} 条结果
      </div>
      <div class="type-statistics">
        <div 
          v-for="(count, type) in typeStatistics" 
          :key="type"
          class="type-stat"
          :class="{ active: selectedType === type }"
          @click="filterByType(type)">
          {{ getTypeLabel(type) }}: {{ count }}
        </div>
      </div>
    </div>

    <!-- 表格控制区 -->
    <div class="column-control">
      <el-button size="small" @click="columnDialogVisible = true">
        列显示控制<i class="el-icon-setting el-icon--right"></i>
      </el-button>
      <el-button type="warning" size="small">脱敏显示</el-button>
      <el-button type="primary" size="small" :disabled="selectedRows.length === 0">导出CSV</el-button>
      <el-button size="small" type="primary" :disabled="selectedRows.length === 0">数据分析</el-button>
    </div>

    <!-- 结果表格 -->
    <el-table
      ref="dataTable"
      :data="filteredResults"
      style="width: 100%"
      border
      stripe
      @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55"></el-table-column>
      <!-- Using store.visibleColumns getter to dynamically render columns -->
      <el-table-column
        v-for="col in store.visibleColumns"
        :key="col"
        :prop="col"
        :label="col">
      </el-table-column>
    </el-table>

    <!-- 列显示控制对话框 -->
    <column-display-dialog
      :visible.sync="columnDialogVisible"
    ></column-display-dialog>
  </div>
</template>

<script>
import { useSearchStore } from '../store/search';
import { computed } from 'vue';
import ColumnDisplayDialog from './ColumnDisplayDialog.vue';

export default {
  name: 'ResultsTable',
  components: {
    ColumnDisplayDialog,
  },
  setup() {
    const store = useSearchStore();
    return { store };
  },
  data() {
    return {
      selectedRows: [],
      columnDialogVisible: false,
      selectedType: null,
    };
  },
  computed: {
    typeStatistics() {
      const stats = {};
      this.store.searchResults.forEach(result => {
        const type = result['数据类型'] || result['数据源'] || '其他';
        stats[type] = (stats[type] || 0) + 1;
      });
      return stats;
    },
    filteredResults() {
      if (!this.selectedType) {
        return this.store.searchResults;
      }
      return this.store.searchResults.filter(result => {
        const type = result['数据类型'] || result['数据源'] || '其他';
        return type === this.selectedType;
      });
    }
  },
  methods: {
    handleSelectionChange(selection) {
      this.selectedRows = selection;
    },
    getTypeLabel(type) {
      const labels = {
        'case': '快响信息',
        'engineering': '工程文件',
        'manual': '手册',
        'faults': '故障报告',
        'r_and_i_record': '部件拆换记录'
      };
      return labels[type] || type;
    },
    filterByType(type) {
      if (this.selectedType === type) {
        this.selectedType = null;
      } else {
        this.selectedType = type;
      }
    },
  },
};
</script>

<style scoped>
/* Styles from table.css */
.el-table {
    margin-top: 10px;
    font-size: 13px;
}

.el-table__body tr:hover > td {
    background-color: #e6f1fc !important;
}

.el-table__body tr.selected-row td {
    background-color: #e6f1fc !important;
}

.el-table th {
    font-size: 13px;
    padding: 4px 0;
}

.el-table td {
    padding: 2px 4px;
    font-size: 12px;
    vertical-align: top !important;
}

.el-table .cell {
    line-height: 18px;
    white-space: pre-wrap !important;
    height: auto !important;
    word-break: break-all;
    padding-top: 4px !important;
}

.narrow-column {
    width: auto !important;
    min-width: 50px !important;
}

/* 表格容器 */
.el-table__body-wrapper {
    overflow-y: auto;
}

/* 结果区域样式 */
.result-section {
    flex: 1;
    background-color: white;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
    padding: 20px;
    margin-top: 20px;
}

/* 结果信息样式 */
.result-info {
    margin: 10px 0;
    color: #606266;
    font-size: 14px;
    font-weight: bold;
}

/* 列控制区域 */
.column-control {
    margin-top: 10px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}

.column-control .el-dropdown {
    margin-right: 10px;
}

/* 列下拉项样式 */
.column-dropdown-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 10px;
}

.column-dropdown-item .el-checkbox {
    margin-right: 0;
}

/* 结果计数容器 */
.result-count-container {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 15px;
}

.total-count {
    margin-right: 15px;
}

/* 类型统计样式 */
.type-statistics {
    display: flex;
    flex-wrap: wrap;
    font-size: 14px;
    color: #666;
}

.type-stat {
    margin-right: 15px;
    padding: 2px 8px;
    background-color: #f0f0f0;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.type-stat:hover {
    background-color: #e0e0e0;
}

.type-stat.active {
    background-color: #409EFF;
    color: white;
}

.el-pagination {
  margin-top: 20px;
  text-align: right;
}

.column-control-dialog .el-checkbox-group {
  display: flex;
  flex-direction: column;
}
</style>
