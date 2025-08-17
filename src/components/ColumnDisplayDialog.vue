<template>
  <el-dialog title="列显示控制" :visible.sync="dialogVisible" width="300px" @close="handleClose">
    <div class="dialog-content">
      <div class="select-all-section">
        <el-checkbox v-model="selectAll" @change="handleSelectAllChange">全选</el-checkbox>
      </div>
      <el-checkbox-group v-model="selectedColumns" @change="handleSelectedChanged">
        <div v-for="col in store.allColumns" :key="col" class="checkbox-item">
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
  name: 'ColumnDisplayDialog',
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
      selectAll: false,
    };
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
      // Load current column visibility settings
      this.selectedColumns = this.store.allColumns.filter(col => this.store.columnVisible[col]);
      this.updateSelectAllState();
    },
    updateSelectAllState() {
      this.selectAll = this.selectedColumns.length === this.store.allColumns.length;
    },
    handleSelectAllChange(value) {
      if (value) {
        this.selectedColumns = [...this.store.allColumns];
      } else {
        this.selectedColumns = [];
      }
    },
    handleSelectedChanged() {
      this.updateSelectAllState();
    },
    handleClose() {
      this.$emit('update:visible', false);
    },
    handleConfirm() {
      // Apply the column visibility settings
      const newColumnVisible = { ...this.store.columnVisible };
      
      // Update visibility for all columns
      this.store.allColumns.forEach(col => {
        newColumnVisible[col] = this.selectedColumns.includes(col);
      });
      
      // Update store
      this.store.columnVisible = newColumnVisible;
      
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

.select-all-section {
  margin-bottom: 15px;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 10px;
}

.checkbox-item {
  margin-bottom: 10px;
}
</style>