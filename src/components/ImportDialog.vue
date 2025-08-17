<template>
  <el-dialog title="手动导入数据" :visible.sync="dialogVisible" width="80%" @close="handleClose">
    <div class="import-dialog-content">
      <!-- Step 1: Data Entry -->
      <div v-if="!importPreview">
        <div class="section data-source-section">
          <h3>选择数据源</h3>
          <el-radio-group v-model="selectedDataSource" @change="handleDataSourceChange">
            <div class="radio-options">
              <el-radio v-for="(label, value) in availableDataSources"
                        :key="value"
                        :label="value">
                {{ label }}
              </el-radio>
            </div>
          </el-radio-group>
        </div>

        <el-table :data="importData" border style="width: 100%" v-loading="loading">
          <el-table-column v-for="header in columnHeaders" :key="header" :prop="header" :label="header">
            <template slot-scope="scope">
              <el-input v-model="scope.row[header]" size="small"></el-input>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template slot-scope="scope">
              <el-button type="danger" icon="el-icon-delete" size="mini" @click="removeRow(scope.$index)"></el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button type="text" icon="el-icon-plus" @click="addRow">添加新行</el-button>
      </div>

      <!-- Step 2: Preview -->
      <div v-if="importPreview">
        <h3>导入预览</h3>
        <p>共检测到 {{ importPreview.total_rows }} 条数据，其中 {{ importPreview.valid_rows }} 条有效，{{ importPreview.invalid_rows }} 条无效。</p>
        <el-table :data="importPreview.preview_rows" border style="width: 100%">
          <el-table-column v-for="col in importPreview.columns" :key="col" :prop="col" :label="col"></el-table-column>
        </el-table>
      </div>
    </div>

    <span slot="footer" class="dialog-footer">
      <!-- Footer for Step 1 -->
      <div v-if="!importPreview">
        <el-button @click="handleClose">取 消</el-button>
        <el-button type="primary" @click="previewImport" :loading="loading" :disabled="!canPreview">预 览</el-button>
      </div>
      <!-- Footer for Step 2 -->
      <div v-if="importPreview">
        <el-button @click="cancelImport">返回修改</el-button>
        <el-button type="success" @click="confirmImport" :loading="loading">确认导入</el-button>
      </div>
    </span>
  </el-dialog>
</template>

<script>
import { useSearchStore } from '../store/search';
import axios from 'axios';

export default {
  name: 'ImportDialog',
  setup() {
    const store = useSearchStore();
    return { store };
  },
  data() {
    return {
      loading: false,
      selectedDataSource: '', // Default data source
      availableDataSources: {},
      columnHeaders: [],
      importData: [],
      importPreview: null,
    };
  },
  computed: {
    dialogVisible: {
      get() {
        return this.store.isImportDialogVisible;
      },
      set(value) {
        if (!value) {
          this.store.closeImportDialog();
        }
      }
    },
    canPreview() {
      return this.importData.some(row => 
        this.columnHeaders.some(header => row[header] && row[header].trim() !== '')
      );
    }
  },
  methods: {
    async fetchAvailableDataSources() {
      this.loading = true;
      try {
        const response = await axios.get('/api/data_source_columns');
        if (response.data.status === 'success') {
          this.availableDataSources = response.data.columns;
          const sources = Object.keys(response.data.columns);
          if (sources.length > 0) {
            // Set default selection and fetch its columns
            this.selectedDataSource = sources[0];
            this.handleDataSourceChange(this.selectedDataSource);
          }
        } else {
          this.$message.error('加载数据源失败: ' + response.data.message);
        }
      } catch (error) {
        this.$message.error('加载数据源时发生错误');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async fetchColumnsForDataSource(dataSource) {
        if (!dataSource) return;
        this.loading = true;
        try {
            const response = await axios.get(`/api/data_columns?source=${dataSource}`);
            if (response.data.success) {
                this.columnHeaders = response.data.columns;
                this.resetTable();
            } else {
                this.$message.error('获取列信息失败: ' + response.data.message);
                this.columnHeaders = []; // Clear headers on failure
            }
        } catch (error) {
            this.$message.error('获取列信息时发生错误');
            this.columnHeaders = []; // Clear headers on error
            console.error(error);
        } finally {
            this.loading = false;
        }
    },
    handleDataSourceChange(dataSource) {
      this.fetchColumnsForDataSource(dataSource);
    },
    resetTable() {
      this.importData = [];
      this.addRow();
    },
    addRow() {
      const newRow = {};
      this.columnHeaders.forEach(col => {
        this.$set(newRow, col, '');
      });
      this.importData.push(newRow);
    },
    removeRow(index) {
      this.importData.splice(index, 1);
      if (this.importData.length === 0) {
        this.addRow();
      }
    },
    async previewImport() {
      if (!this.canPreview) {
        this.$message.warning('请输入有效数据后再预览');
        return;
      }
      this.loading = true;
      const validRows = this.importData.filter(row => 
        this.columnHeaders.some(header => row[header] && row[header].trim() !== '')
      );

      try {
        const response = await axios.post(`/api/import/${this.selectedDataSource}/preview`, {
          data: validRows,
          dataSource: this.selectedDataSource
        });
        if (response.data.status === 'success') {
          this.importPreview = {
            ...response.data.preview,
            temp_id: response.data.temp_id,
            preview_rows: validRows,
            columns: this.columnHeaders
          };
          this.$message.success('预览成功');
        } else {
          this.$message.error('预览失败: ' + response.data.message);
        }
      } catch (error) {
        this.$message.error('预览时发生错误');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async confirmImport() {
      if (!this.importPreview || !this.importPreview.temp_id) {
        this.$message.warning('没有可确认的预览数据');
        return;
      }
      this.loading = true;
      try {
        const response = await axios.post(`/api/import/${this.selectedDataSource}/confirm`, {
          temp_id: this.importPreview.temp_id,
          dataSource: this.selectedDataSource
        });
        if (response.data.status === 'success') {
          this.$message.success('导入成功！');
          this.handleClose(); // Close dialog on success
        } else {
          this.$message.error('导入失败: ' + response.data.message);
        }
      } catch (error) {
        this.$message.error('确认导入时发生错误');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    cancelImport() {
      this.importPreview = null;
    },
    handleClose() {
      this.store.closeImportDialog();
      // Reset state
      this.importPreview = null;
      this.columnHeaders = [];
      this.importData = [];
      this.selectedDataSource = '';
      this.availableDataSources = {};
    }
  },
  mounted() {
    // Fetch available data sources when component is first mounted
    this.fetchAvailableDataSources();
  },
  watch: {
    // Watch for the dialog becoming visible to load initial data if it hasn't been loaded
    dialogVisible(newValue) {
      if (newValue && Object.keys(this.availableDataSources).length === 0) {
        this.fetchAvailableDataSources();
      }
    }
  }
};
</script>

<style scoped>
.import-dialog-content {
  max-height: 60vh;
  overflow-y: auto;
}

.section {
    margin-bottom: 20px;
}

.section h3 {
    margin: 0 0 15px 0;
    font-size: 16px;
    color: #606266;
    font-weight: 600;
}

.data-source-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 4px;
    border: 1px solid #EBEEF5;
}

.radio-options {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-top: 10px;
}
</style>
