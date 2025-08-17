<template>
  <el-dialog title="搜索范围设置" :visible.sync="dialogVisible" width="300px" @close="handleClose">
    <div class="dialog-content">
      <el-checkbox-group v-model="selectedColumns">
        <div v-for="col in searchableColumns" :key="col" class="checkbox-item">
          <el-checkbox :label="col">{{ col }}</el-checkbox>
        </div>
      </el-checkbox-group>
    </div>
    <span slot="footer" class="dialog-footer">
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </span>
  </el-dialog>
</template>

<script>
import { useSearchStore } from '../store/search';

export default {
  name: 'SearchScopeDialog',
  setup() {
    const store = useSearchStore();
    return { store };
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialogVisible: this.visible,
      selectedColumns: [],
    };
  },
  computed: {
    searchableColumns() {
      // Get searchable columns for current data source
      const dataSource = this.store.dataSource;
      const searchableColumnsMap = {
        'case': ['标题', '问题描述', '答复详情', '客户期望'],
        'engineering': ['文件名称', '原因和说明', '原文文本'],
        'manual': ['标题', '问题描述', '答复详情', '客户期望'],
        'faults': ['问题描述', '排故措施'],
        'r_and_i_record': ['拆下原因', '故障描述']
      };
      return searchableColumnsMap[dataSource] || [];
    },
  },
  watch: {
    visible(newVal) {
      this.dialogVisible = newVal;
      if (newVal) {
        this.loadCurrentSettings();
      }
    },
  },
  methods: {
    loadCurrentSettings() {
      // Load current similarity search columns
      this.selectedColumns = [...this.store.similaritySearchColumns];
      
      // If no columns are selected, select all searchable columns
      if (this.selectedColumns.length === 0) {
        this.selectedColumns = [...this.searchableColumns];
      }
    },
    handleClose() {
      this.$emit('update:visible', false);
    },
    handleConfirm() {
      // Apply the search scope settings
      this.store.similaritySearchColumns = [...this.selectedColumns];
      this.handleClose();
    },
  },
};
</script>

<style scoped>
.dialog-content {
  max-height: 400px;
  overflow-y: auto;
}

.checkbox-item {
  margin-bottom: 10px;
}
</style>