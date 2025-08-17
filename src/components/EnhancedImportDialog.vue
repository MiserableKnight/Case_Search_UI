<template>
  <el-dialog
    title="数据导入"
    :visible.sync="dialogVisible"
    width="30%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose">
    <div class="import-dialog-content">
      <div class="import-header">
        <!-- 数据源选择 -->
        <div class="import-source-select">
          <div class="section-title">选择数据源</div>
          <el-radio-group v-model="importSettings.dataSource">
            <div class="radio-options">
              <el-radio 
                v-for="(label, value) in importDataSourceOptions"
                :key="value"
                :label="value">
                {{ label }}
              </el-radio>
            </div>
          </el-radio-group>
        </div>

        <!-- 文件上传区域 -->
        <div class="upload-section">
          <el-upload
            class="upload-area"
            drag
            :action="uploadUrl"
            :data="{ dataSource: importSettings.dataSource }"
            :before-upload="handleBeforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :show-file-list="false"
            :multiple="false">
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击选择文件</em>
            </div>
            <div class="el-upload__tip" slot="tip">
              支持上传 .xlsx, .xls 格式的文件
            </div>
          </el-upload>
        </div>
      </div>

      <!-- 预览区域 -->
      <div v-if="importSettings.previewData" class="preview-area">
        <!-- 数据统计信息 -->
        <el-card class="preview-info">
          <div slot="header">
            <span class="card-title">数据统计</span>
          </div>
          <div class="preview-stats">
            <p>上传数据：{{ importSettings.previewData.uploaded_count }} 条</p>
            <p>实际新增：{{ importSettings.previewData.new_count }} 条</p>
            <p>重复数据：{{ importSettings.previewData.uploaded_count - importSettings.previewData.new_count }} 条</p>
            <p>原有数据：{{ importSettings.previewData.original_count }} 条</p>
            <p>变更后数据：{{ importSettings.previewData.original_count + importSettings.previewData.new_count }} 条</p>
          </div>
        </el-card>
      </div>
    </div>
    <div slot="footer" class="dialog-footer">
      <el-button @click="handleClose">取消</el-button>
      <el-button type="info" @click="goToDataImportPage">手动导入</el-button>
      <el-button
        type="primary"
        @click="confirmImport"
        :disabled="!importSettings.previewData">
        确认导入
      </el-button>
    </div>
  </el-dialog>
</template>

<script>
import { useSearchStore } from '../store/search';
import axios from 'axios';

export default {
  name: 'EnhancedImportDialog',
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
      importSettings: {
        dataSource: 'case',
        previewData: null,
      },
      importDataSourceOptions: {
        'case': '快响信息',
        'engineering': '工程文件',
        'manual': '手册',
        'faults': '故障报告',
        'r_and_i_record': '部件拆换记录'
      },
    };
  },
  computed: {
    uploadUrl() {
      return `/api/import/${this.importSettings.dataSource}/import`;
    },
  },
  watch: {
    visible(newVal) {
      this.dialogVisible = newVal;
      if (newVal) {
        this.resetImportSettings();
      }
    },
  },
  methods: {
    resetImportSettings() {
      this.importSettings = {
        dataSource: this.store.dataSource,
        previewData: null,
      };
    },
    handleBeforeUpload(file) {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                     file.type === 'application/vnd.ms-excel';
      
      if (!isExcel) {
        this.$message.error('只能上传 Excel 文件！');
        return false;
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        this.$message.error('文件大小不能超过 10MB！');
        return false;
      }
      
      return true;
    },
    handleUploadSuccess(response, file) {
      if (response.status === 'success') {
        this.$message.success('文件上传成功');
        this.importSettings.previewData = response.data;
      } else {
        this.$message.error(response.message || '文件上传失败');
      }
    },
    handleUploadError(error) {
      console.error('Upload error:', error);
      this.$message.error('文件上传失败');
    },
    confirmImport() {
      if (!this.importSettings.previewData) {
        this.$message.warning('请先上传文件');
        return;
      }
      
      // Confirm import with the temp_id from preview data
      axios.post(`/api/import/${this.importSettings.dataSource}/confirm_import`, {
        temp_id: this.importSettings.previewData.temp_id
      })
      .then(response => {
        if (response.data.status === 'success') {
          this.$message.success('数据导入成功');
          this.handleClose();
          // Refresh data or trigger search update
          this.store.changeDataSource(this.store.dataSource);
        } else {
          this.$message.error(response.data.message || '导入失败');
        }
      })
      .catch(error => {
        console.error('Import error:', error);
        this.$message.error('导入失败');
      });
    },
    goToDataImportPage() {
      // Navigate to manual import page
      window.open('/import', '_blank');
    },
    handleClose() {
      this.$emit('update:visible', false);
    },
  },
};
</script>

<style scoped>
.import-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.import-header {
  display: flex;
  gap: 20px;
}

.import-source-select {
  flex: 1;
  padding: 15px;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
}

.upload-section {
  flex: 1.5;
}

.section-title {
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.radio-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-area {
  border: 2px dashed #DCDFE6;
  border-radius: 6px;
  padding: 20px;
  text-align: center;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #409EFF;
}

.preview-area {
  margin-top: 20px;
}

.preview-info {
  margin-bottom: 20px;
}

.card-title {
  font-weight: bold;
  color: #303133;
}

.preview-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-stats p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>