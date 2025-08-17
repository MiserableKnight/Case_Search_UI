<template>
  <el-dialog :title="title" :visible.sync="dialogVisible" :width="dialogWidth" @close="handleClose">
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

      <!-- Sensitive Word Management -->
      <div v-if="mode === 'sensitiveWords'" class="sensitive-word-manager">
        <div class="add-word-section" style="display: flex; align-items: center; margin-bottom: 10px;">
          <el-select v-model="selectedCategory" style="width: 120px; margin-right: -1px;">
            <el-option v-for="cat in categories" :key="cat" :label="categoryLabels[cat]" :value="cat"></el-option>
          </el-select>
          <el-input v-model="newWord" placeholder="输入敏感词" style="width: 160px; margin-right: 15px;"></el-input>
          <el-button type="primary" @click="addSensitiveWord">添加</el-button>
        </div>
        <el-tabs type="card" v-model="activeCategory">
          <el-tab-pane v-for="cat in categories" :key="cat" :label="categoryLabels[cat]" :name="cat"></el-tab-pane>
        </el-tabs>
        <div class="sensitive-word-list" style="max-height: 250px; overflow-y: auto; margin-top: 10px; border: 1px solid #EBEEF5; border-radius: 4px;">
          <table style="width: 100%; border-collapse: collapse; table-layout: fixed;">
            <thead>
              <tr style="background-color: #F5F7FA; height: 36px;">
                <th style="padding-left: 15px; text-align: left; font-weight: normal;">敏感词</th>
                <th style="width: 80px; text-align: center; font-weight: normal;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(word, index) in sensitiveWords[activeCategory] || []" :key="index" style="border-bottom: 1px solid #EBEEF5; height: 36px;">
                <td style="padding-left: 15px; text-align: left;">{{ typeof word === 'object' ? word.word : word }}</td>
                <td style="width: 80px; text-align: center;">
                  <el-button type="danger" size="mini" style="padding: 3px 8px; font-size: 12px;" @click="removeSensitiveWord(typeof word === 'object' ? word.word : word, activeCategory)">删除</el-button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
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
      type: String, // 'dataSource', 'aircraftTypes', or 'sensitiveWords'
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
      // Sensitive Words Data
      newWord: '',
      selectedCategory: 'registration_numbers',
      activeCategory: 'registration_numbers',
      categories: ['registration_numbers', 'organizations', 'aircraft', 'locations', 'other'],
      categoryLabels: {
        'registration_numbers': '机号/序列号',
        'organizations': '单位/部门',
        'aircraft': '机型',
        'locations': '地点',
        'other': '其他'
      },
      sensitiveWords: {},
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
      const titles = {
        dataSource: '选择数据源',
        aircraftTypes: '选择机型',
        sensitiveWords: '敏感词管理',
      };
      return titles[this.mode] || '设置';
    },
    dialogWidth() {
      return this.mode === 'sensitiveWords' ? '575px' : '300px';
    }
  },
  methods: {
    syncStateWithStore() {
      if (this.mode === 'dataSource') {
        this.tempDataSource = this.store.dataSource;
      } else if (this.mode === 'aircraftTypes') {
        this.tempAircraftTypes = [...this.store.aircraftTypes];
        this.updateSelectAllState();
      } else if (this.mode === 'sensitiveWords') {
        this.loadSensitiveWords();
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
      // For sensitive words, changes are saved via API, so just close.
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

    // Sensitive Word Methods
    loadSensitiveWords() {
      fetch('/api/sensitive_words')
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            this.categories.forEach(category => {
              this.$set(this.sensitiveWords, category, data.words[category] || []);
            });
          } else {
            this.$message.error('加载敏感词失败');
          }
        })
        .catch(() => {
          this.$message.error('加载敏感词失败');
        });
    },
    addSensitiveWord() {
      const word = this.newWord.trim();
      if (!word) {
        this.$message.warning('请输入敏感词');
        return;
      }

      const isWordExists = Object.values(this.sensitiveWords).some(
        categoryWords => categoryWords.some(item => (typeof item === 'object' ? item.word : item) === word)
      );

      if (isWordExists) {
        this.$message.error('该敏感词已存在于词库中');
        return;
      }

      fetch('/api/sensitive_words', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: word, category: this.selectedCategory }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          this.$message.success('敏感词添加成功');
          this.newWord = '';
          this.loadSensitiveWords();
        } else {
          this.$message.error(data.message || '添加失败');
        }
      })
      .catch(() => {
        this.$message.error('添加敏感词失败');
      });
    },
    removeSensitiveWord(word, category) {
      this.$confirm('确定要删除这个敏感词吗？', '提示', { type: 'warning' })
        .then(() => {
          fetch('/api/sensitive_words', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word, category }),
          })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'success') {
              this.$message.success('删除成功');
              this.loadSensitiveWords();
            } else {
              this.$message.error(data.message || '删除失败');
            }
          })
          .catch(() => {
            this.$message.error('删除失败');
          });
        }).catch(() => {});
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
