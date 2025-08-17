<template>
  <el-dialog title="手动导入数据" v-model="dialogVisible" width="80%" @close="handleClose">
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
            <template #default="scope">
              <el-input v-model="scope.row[header]" size="small"></el-input>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="scope">
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

    <template #footer>
      <span class="dialog-footer">
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
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { useSearchStore } from '../store/search';
import axios from 'axios';

export default {
  name: 'ImportDialog',
  setup() {
    const store = useSearchStore();
    
    const loading = ref(false);
    const selectedDataSource = ref('');
    const availableDataSources = ref({});
    const columnHeaders = ref([]);
    const importData = ref([]);
    const importPreview = ref(null);
    
    const dialogVisible = computed({
      get() {
        return store.isImportDialogVisible;
      },
      set(value) {
        if (!value) {
          store.closeImportDialog();
        }
      }
    });
    
    const canPreview = computed(() => {
      return importData.value.some(row => 
        columnHeaders.value.some(header => row[header] && row[header].trim() !== '')
      );
    });

    const fetchAvailableDataSources = async () => {
      loading.value = true;
      try {
        const response = await axios.get('/api/data_source_columns');
        if (response.data.status === 'success') {
          availableDataSources.value = response.data.columns;
          const sources = Object.keys(response.data.columns);
          if (sources.length > 0) {
            selectedDataSource.value = sources[0];
            handleDataSourceChange(selectedDataSource.value);
          }
        } else {
          ElMessage.error('加载数据源失败: ' + response.data.message);
        }
      } catch (error) {
        ElMessage.error('加载数据源时发生错误');
        console.error(error);
      } finally {
        loading.value = false;
      }
    };

    const fetchColumnsForDataSource = async (dataSource) => {
      if (!dataSource) return;
      loading.value = true;
      try {
        const response = await axios.get(`/api/data_columns?source=${dataSource}`);
        if (response.data.success) {
          columnHeaders.value = response.data.columns;
          resetTable();
        } else {
          ElMessage.error('获取列信息失败: ' + response.data.message);
          columnHeaders.value = [];
        }
      } catch (error) {
        ElMessage.error('获取列信息时发生错误');
        columnHeaders.value = [];
        console.error(error);
      } finally {
        loading.value = false;
      }
    };

    const handleDataSourceChange = (dataSource) => {
      fetchColumnsForDataSource(dataSource);
    };

    const resetTable = () => {
      importData.value = [];
      addRow();
    };

    const addRow = () => {
      const newRow = {};
      columnHeaders.value.forEach(col => {
        newRow[col] = '';
      });
      importData.value.push(newRow);
    };

    const removeRow = (index) => {
      importData.value.splice(index, 1);
      if (importData.value.length === 0) {
        addRow();
      }
    };

    const previewImport = async () => {
      if (!canPreview.value) {
        ElMessage.warning('请输入有效数据后再预览');
        return;
      }
      loading.value = true;
      const validRows = importData.value.filter(row => 
        columnHeaders.value.some(header => row[header] && row[header].trim() !== '')
      );

      try {
        const response = await axios.post(`/api/import/${selectedDataSource.value}/preview`, {
          data: validRows,
          dataSource: selectedDataSource.value
        });
        if (response.data.status === 'success') {
          importPreview.value = {
            ...response.data.preview,
            temp_id: response.data.temp_id,
            preview_rows: validRows,
            columns: columnHeaders.value
          };
          ElMessage.success('预览成功');
        } else {
          ElMessage.error('预览失败: ' + response.data.message);
        }
      } catch (error) {
        ElMessage.error('预览时发生错误');
        console.error(error);
      } finally {
        loading.value = false;
      }
    };

    const confirmImport = async () => {
      if (!importPreview.value || !importPreview.value.temp_id) {
        ElMessage.warning('没有可确认的预览数据');
        return;
      }
      loading.value = true;
      try {
        const response = await axios.post(`/api/import/${selectedDataSource.value}/confirm`, {
          temp_id: importPreview.value.temp_id,
          dataSource: selectedDataSource.value
        });
        if (response.data.status === 'success') {
          ElMessage.success('导入成功！');
          handleClose();
        } else {
          ElMessage.error('导入失败: ' + response.data.message);
        }
      } catch (error) {
        ElMessage.error('确认导入时发生错误');
        console.error(error);
      } finally {
        loading.value = false;
      }
    };

    const cancelImport = () => {
      importPreview.value = null;
    };

    const handleClose = () => {
      store.closeImportDialog();
      importPreview.value = null;
      columnHeaders.value = [];
      importData.value = [];
      selectedDataSource.value = '';
      availableDataSources.value = {};
    };

    onMounted(() => {
      fetchAvailableDataSources();
    });

    watch(dialogVisible, (newValue) => {
      if (newValue && Object.keys(availableDataSources.value).length === 0) {
        fetchAvailableDataSources();
      }
    });

    return {
      store,
      loading,
      selectedDataSource,
      availableDataSources,
      columnHeaders,
      importData,
      importPreview,
      dialogVisible,
      canPreview,
      fetchAvailableDataSources,
      fetchColumnsForDataSource,
      handleDataSourceChange,
      resetTable,
      addRow,
      removeRow,
      previewImport,
      confirmImport,
      cancelImport,
      handleClose,
    };
  },
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
