<template>
  <el-dialog :title="title" :visible.sync="dialogVisible" width="300px" @close="handleClose">
    <div class="dialog-content">
      <!-- Data Source Selection -->
      <div v-if="mode === 'dataSource'">
        <el-radio-group v-model="tempDataSource">
          <div v-for="ds in store.dataSources" :key="ds.value" class="radio-item">
            <el-radio :label="ds.value">{{ ds.label }}</el-radio>
          </div>
        </el-radio-group>
      </div>

      <!-- Aircraft Types Selection -->
      <div v-if="mode === 'aircraftTypes'">
        <div class="checkbox-all-item">
          <el-checkbox v-model="selectAll" @change="handleSelectAllChange">全选</el-checkbox>
        </div>
        <el-checkbox-group v-model="tempAircraftTypes" @change="handleSelectionChange">
          <div v-for="type in aircraftTypeOptions" :key="type" class="checkbox-item">
            <el-checkbox :label="type">{{ type }}</el-checkbox>
          </div>
        </el-checkbox-group>
      </div>
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
  name: 'SettingsDialog',
  setup() {
    const store = useSearchStore();
    return { store };
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    mode: {
      type: String, // 'dataSource' or 'aircraftTypes'
      required: true,
    },
  },
  data() {
    return {
      dialogVisible: this.visible,
      tempDataSource: '',
      tempAircraftTypes: [],
      aircraftTypeOptions: ["ARJ21", "C919", "无"],
      selectAll: false,
    };
  },
  watch: {
    visible(newVal) {
      this.dialogVisible = newVal;
      if (newVal) {
        this.syncStateWithStore();
      }
    },
  },
  computed: {
    title() {
      return this.mode === 'dataSource' ? '选择数据源' : '选择机型';
    },
  },
  methods: {
    syncStateWithStore() {
      if (this.mode === 'dataSource') {
        this.tempDataSource = this.store.dataSource;
      } else if (this.mode === 'aircraftTypes') {
        this.tempAircraftTypes = [...this.store.aircraftTypes];
        this.updateSelectAllState();
      }
    },
    handleClose() {
      this.$emit('update:visible', false);
    },
    handleConfirm() {
      if (this.mode === 'dataSource') {
        this.store.changeDataSource(this.tempDataSource);
      } else if (this.mode === 'aircraftTypes') {
        this.store.setAircraftTypes(this.tempAircraftTypes);
      }
      this.handleClose();
    },
    handleSelectAllChange(value) {
      this.tempAircraftTypes = value ? this.aircraftTypeOptions : [];
    },
    handleSelectionChange() {
      this.updateSelectAllState();
    },
    updateSelectAllState() {
      this.selectAll = this.tempAircraftTypes.length === this.aircraftTypeOptions.length;
    },
  },
};
</script>

<style scoped>
.dialog-content {
  max-height: 400px;
  overflow-y: auto;
}
.radio-item, .checkbox-item {
  margin-bottom: 10px;
}
.checkbox-all-item {
  margin-bottom: 15px;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 10px;
}
</style>
