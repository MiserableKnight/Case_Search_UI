<template>
  <div class="search-section" @keyup.enter="submitSearch">
    <!-- 关键字搜索 -->
    <div class="search-block keyword-search">
      <div class="block-title">关键字搜索</div>
      <div class="search-cards">
        <div v-for="(level, idx) in store.searchLevels" :key="idx" class="search-card">
          <div class="search-content">
            <div class="search-inputs">
              <el-input v-model="level.keywords" placeholder="请输入关键字"></el-input>
              <el-select v-model="level.column_name" multiple collapse-tags placeholder="选择搜索列" @change="handleColumnSelectChange($event, level)">
                <el-option key="__select_all__" label="全选" value="__select_all__"></el-option>
                <el-option v-for="col in store.columns" :key="col" :label="col" :value="col"></el-option>
              </el-select>
            </div>
            <div class="search-controls">
              <el-radio-group v-model="level.logic">
                <el-radio label="and">与</el-radio>
                <el-radio label="or">或</el-radio>
              </el-radio-group>
              <div class="switch-with-label">
                <el-switch v-model="level.negative_filtering"></el-switch>
                <span class="switch-label">反向过滤</span>
              </div>
            </div>
          </div>
          <div class="card-actions">
            <span v-if="idx === 0" class="action-btn" @click="store.addSearchLevel" title="添加搜索条件">
              <i class="el-icon-plus"></i>
            </span>
            <span v-if="idx > 0" class="action-btn delete" @click="store.removeSearchLevel(idx)" title="删除">
              <i class="el-icon-close"></i>
            </span>
          </div>
        </div>
      </div>
      <div class="buttons-section">
        <el-button type="primary" @click="submitSearch" :loading="store.loading">搜索</el-button>
        <el-button @click="resetForm">重置</el-button>
      </div>
    </div>

    <!-- 按内容搜索 (Simplified for now) -->
    <div class="search-block similarity-search">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div class="block-title" style="margin-bottom: 0;">按相似度搜索</div>
        </div>
        <div class="content-search">
            <el-input type="textarea" :rows="8" placeholder="请输入要搜索的内容"></el-input>
            <div style="text-align: right;">
                <el-button type="primary">开始搜索</el-button>
            </div>
        </div>
    </div>

    <!-- 默认搜索设置 (Simplified for now) -->
    <div class="search-block default-settings">
        <div class="block-title">默认搜索设置</div>
        <div class="content-search">
            <div class="default-search-controls">
                <div class="control-item">
                    <span class="control-label">数据源：</span>
                    <el-select v-model="store.dataSource" @change="handleDataSourceChange">
                      <el-option v-for="source in store.dataSources" :key="source.value" :label="source.label" :value="source.value"></el-option>
                    </el-select>
                </div>
                <div class="control-item">
                    <span class="control-label">数据导入：</span>
                    <el-button type="primary" size="small" style="width: 120px;">导入数据<i class="el-icon-upload el-icon--right"></i></el-button>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script>
import { useSearchStore } from '../store/search';

export default {
  name: 'SearchForm',
  setup() {
    const store = useSearchStore();
    return { store };
  },
  methods: {
    handleDataSourceChange(dataSource) {
      this.store.changeDataSource(dataSource);
    },
    submitSearch() {
      this.store.performSearch();
    },
    resetForm() {
      // When resetting, we just re-trigger the logic for the current data source
      this.store.changeDataSource(this.store.dataSource);
    },
    handleColumnSelectChange(selected, level) {
      const allColumns = this.store.columns.map(c => c); // Create a copy
      if (selected.includes('__select_all__')) {
        level.column_name = allColumns;
      } else if (selected.length === allColumns.length - 1 && !selected.includes('__select_all__')) {
        // This logic handles the case where user deselects 'Select All'
        // It might need adjustment based on exact UX requirements
      }
    }
  },
};
</script>

<style scoped>
/* Styles from search.css */
.search-section {
    margin-bottom: 5px;
    padding: 20px;
    background-color: white;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
    display: flex;
    gap: 20px;
}

.search-block {
    flex: 1;
    min-width: 0;
    border: 1px solid #EBEEF5;
    border-radius: 4px;
    padding: 15px;
}

.search-block.default-settings {
    flex: 0.67;
}

.search-block.keyword-search {
    flex: 1.83;
}

.search-block.similarity-search {
    flex: 1;
}

.block-title {
    font-size: 16px;
    color: #303133;
    margin-bottom: 15px;
    font-weight: bold;
}

.search-cards {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.search-card {
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: white;
    border: 1px solid #EBEEF5;
    border-radius: 4px;
}

.search-content {
    display: flex;
    align-items: center;
    gap: 20px;
    flex: 1;
}

.search-inputs {
    display: flex;
    gap: 10px;
    align-items: center;
    flex: 1;
}

.search-controls {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-right: 40px;
}

.switch-with-label {
    display: flex;
    align-items: center;
    gap: 5px;
}

.switch-label {
    font-size: 13px;
    color: #606266;
}

.card-actions {
    position: absolute;
    right: 5px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    gap: 5px;
}

.action-btn {
    padding: 4px 8px;
    cursor: pointer;
    color: #909399;
    transition: all 0.3s;
    border: 1px solid #DCDFE6;
    border-radius: 4px;
    background-color: #fff;
}

.action-btn:hover {
    color: #409EFF;
    border-color: #409EFF;
    background-color: #ecf5ff;
}

.action-btn.delete:hover {
    color: #F56C6C;
    border-color: #F56C6C;
    background-color: #fef0f0;
}

.buttons-section {
    margin-top: 15px;
    display: flex;
    justify-content: center;
    gap: 10px;
}

.default-search-controls {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.control-item {
    display: flex;
    align-items: center;
    gap: 10px;
}

.control-label {
    font-size: 14px;
    color: #606266;
    width: 80px;
}

.control-item .el-select {
    flex: 1;
}

/* 搜索逻辑控制 */
.search-logic {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 10px;
}

/* 反向过滤控制 */
.negative-filter {
    display: flex;
    align-items: center;
    gap: 8px;
}

.negative-text {
    font-size: 13px;
    color: #606266;
}

/* 内容搜索区域 */
.content-search {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.content-search .el-input {
    width: 100%;
}

.similarity-btn {
    align-self: flex-end;
}

/* 统计控制 */
.statistics-controls {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-bottom: 15px;
}

.axis-select {
    display: flex;
    align-items: center;
    gap: 10px;
}

.axis-label {
    font-size: 14px;
    color: #606266;
    width: 40px;
}

.axis-select .el-select {
    flex: 1;
}

.statistics-btn {
    width: 100%;
}
</style>
