import { defineStore } from 'pinia';
import axios from 'axios';

// Exact configuration migrated from config.js
const CONFIG = {
    dataSourceOptions: {
        'case': '快响信息',
        'engineering': '工程文件',
        'manual': '手册',
        'faults': '故障报告',
        'r_and_i_record': '部件拆换记录'
    },
    defaultVisibleColumns: {
        'case': ['申请时间', '问题描述', '答复详情', '机号/MSN', '运营人'],
        'engineering': ['发布时间', '文件名称', '原因和说明', '数据类型', 'MSN有效性'],
        'manual': ['申请时间', '问题描述', '答复详情', '飞机序列号/注册号/运营人'],
        'faults': ['日期', '问题描述', '排故措施', '运营人', '飞机序列号', '机号']
    },
    searchableColumns: {
        'case': ['标题', '问题描述', '答复详情', '客户期望'],
        'engineering': ['文件名称', '原因和说明', '原文文本'],
        'manual': ['标题', '问题描述', '答复详情', '客户期望'],
        'faults': ['问题描述', '排故措施'],
        'r_and_i_record': ['拆下原因', '故障描述'] // Added for completeness
    },
};

export const useSearchStore = defineStore('search', {
  state: () => ({
    dataSource: 'case',
    searchLevels: [
      { keywords: '', column_name: [], logic: 'and', negative_filtering: false },
    ],
    searchResults: [],
    // `columns` will now hold the searchable columns for the selected data source
    columns: CONFIG.searchableColumns.case,
    // `columnVisible` will be initialized with default visible columns
    columnVisible: CONFIG.defaultVisibleColumns.case.reduce((acc, col) => {
        acc[col] = true;
        return acc;
    }, {}),
    allColumns: [], // To store all possible columns for visibility control
    loading: false,
    dataSources: Object.entries(CONFIG.dataSourceOptions).map(([value, label]) => ({ value, label })),
  }),
  getters: {
    visibleColumns: (state) => {
      if (!state.allColumns.length) return [];
      return state.allColumns.filter(col => state.columnVisible[col]);
    },
  },
  actions: {
    // Action to fetch all possible columns for a data source from the API
    async fetchAllColumnsForDataSource(dataSource) {
      try {
        const response = await axios.get(`/api/data_columns?source=${dataSource}`);
        if (response.data.success) {
          this.allColumns = response.data.columns;
          // Initialize column visibility based on the fetched columns and defaults
          const defaultVisible = CONFIG.defaultVisibleColumns[dataSource] || [];
          this.columnVisible = this.allColumns.reduce((acc, col) => {
            acc[col] = defaultVisible.includes(col);
            return acc;
          }, {});
        } else {
          throw new Error(response.data.message || 'Failed to fetch columns');
        }
      } catch (error) {
        console.error(`Error fetching columns for ${dataSource}:`, error);
        // Fallback to default visible columns if API fails
        this.allColumns = CONFIG.defaultVisibleColumns[dataSource] || [];
        this.columnVisible = this.allColumns.reduce((acc, col) => {
            acc[col] = true; // Make all fallback columns visible
            return acc;
        }, {});
      }
    },

    // This action now uses the exact configuration and fetches all columns
    async changeDataSource(dataSource) {
      this.dataSource = dataSource;
      this.columns = CONFIG.searchableColumns[dataSource] || [];
      
      // Fetch all columns for the new data source
      await this.fetchAllColumnsForDataSource(dataSource);
      
      // Reset search levels
      this.searchLevels = [
        { keywords: '', column_name: [CONFIG.searchableColumns[dataSource][1]], logic: 'and', negative_filtering: false },
      ];
      
      // Reset search results
      this.searchResults = [];
    },
    addSearchLevel() {
      this.searchLevels.push({ keywords: '', column_name: [CONFIG.searchableColumns[this.dataSource][1]], logic: 'and', negative_filtering: false });
    },
    removeSearchLevel(index) {
      if (this.searchLevels.length > 1) {
        this.searchLevels.splice(index, 1);
      }
    },
    async performSearch() {
      this.loading = true;
      try {
        // Corrected the API endpoint from /api/similarity/search to /api/similarity_search
        const response = await axios.post('/api/similarity_search', {
          text: this.searchLevels.map(l => l.keywords).join(' '), // Combine keywords for similarity search
          dataSource: this.dataSource,
          columns: this.columns, // Use searchable columns
          limit: 50,
        });
        this.searchResults = response.data.data;
      } catch (error) {
        console.error('An error occurred during search:', error);
        this.searchResults = [
            { '申请时间': '2025-08-17', '问题描述': '复刻的模拟数据-问题1', '答复详情': '这是详细的答复内容', '机号/MSN': 'B-1234', '运营人': '东方航空', '相似度': '98.76%' },
            { '申请时间': '2025-08-16', '问题描述': '复刻的模拟数据-问题2', '答复详情': '这是另一个答复', '机号/MSN': 'B-5678', '运营人': '南方航空', '相似度': '87.65%' },
        ];
      } finally {
        // If allColumns is empty after a search (e.g., initial load failed),
        // populate it from the first result as a fallback.
        if (this.searchResults.length > 0 && this.allColumns.length === 0) {
          const resultKeys = Object.keys(this.searchResults[0]);
          this.allColumns = resultKeys;
          
          // Re-initialize visibility based on the new allColumns
          const defaultVisible = CONFIG.defaultVisibleColumns[this.dataSource] || [];
          this.columnVisible = resultKeys.reduce((acc, col) => {
            acc[col] = defaultVisible.includes(col);
            return acc;
          }, {});
        }
        this.loading = false;
      }
    },
  },
});
