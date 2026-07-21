<template>
    <div class="panel">
        <div class="panel-header">
            <div class="nt-block-title" style="margin-bottom: 0">相似度搜索</div>
            <el-button text size="small" :icon="Setting" @click="dialogVisible = true">
                搜索范围设置
            </el-button>
        </div>
        <el-input
            v-model="store.contentSearch.text"
            type="textarea"
            :rows="5"
            placeholder="请输入要搜索的内容，系统会查找相似的历史问题"
        />
        <div class="button-row">
            <el-button
                type="primary"
                :loading="store.loadingSimilarity"
                :disabled="!store.contentSearch.selectedColumns.length"
                @click="store.similaritySearch()"
            >
                开始搜索
            </el-button>
        </div>

        <SearchColumnsDialog v-model="dialogVisible" />
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import { useSearchStore } from '../stores/search'
import SearchColumnsDialog from './dialogs/SearchColumnsDialog.vue'

const store = useSearchStore()
const dialogVisible = ref(false)
</script>

<style scoped>
.panel {
    background: var(--nt-bg);
    border: 1px solid var(--nt-border-light);
    border-radius: var(--nt-radius-md);
    padding: 16px;
}
.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.button-row {
    display: flex;
    justify-content: flex-end;
    margin-top: 10px;
}
</style>
