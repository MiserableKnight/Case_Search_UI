<template>
    <div class="panel">
        <div class="nt-block-title">关键字搜索</div>

        <div
            v-for="(level, idx) in store.searchLevels"
            :key="idx"
            class="level-card"
        >
            <div class="level-main">
                <el-input
                    v-model="level.keywords"
                    placeholder="请输入关键字，多个关键字用逗号分隔"
                    clearable
                    @keyup.enter="store.search()"
                />
                <el-select
                    :model-value="level.column_name"
                    multiple
                    collapse-tags
                    collapse-tags-tooltip
                    placeholder="选择搜索列"
                    class="level-columns"
                    @update:model-value="store.handleColumnSelectChange($event, level)"
                >
                    <el-option label="全选" value="__select_all__" />
                    <el-option
                        v-for="col in columnOptions"
                        :key="col"
                        :label="col"
                        :value="col"
                    />
                </el-select>
                <div class="level-controls">
                    <el-radio-group v-model="level.logic" size="small">
                        <el-radio-button value="and">与</el-radio-button>
                        <el-radio-button value="or">或</el-radio-button>
                    </el-radio-group>
                    <div class="negative-switch">
                        <el-switch v-model="level.negative_filtering" />
                        <span class="switch-label">反向过滤</span>
                    </div>
                </div>
            </div>
            <div class="level-actions">
                <el-button
                    v-if="idx === 0"
                    text
                    :icon="Plus"
                    title="添加搜索条件"
                    @click="store.addLevel()"
                />
                <el-button
                    v-if="idx > 0"
                    text
                    :icon="Close"
                    title="删除"
                    @click="store.removeLevel(idx)"
                />
            </div>
        </div>

        <div class="button-row">
            <el-button type="primary" :loading="store.loading" @click="store.search()">
                搜索
            </el-button>
            <el-button @click="store.resetForm()">重置</el-button>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, Close } from '@element-plus/icons-vue'
import { useSearchStore } from '../stores/search'

const store = useSearchStore()
const columnOptions = computed(() => store.dataSourceColumns[store.dataSource] || [])
</script>

<style scoped>
.panel {
    background: var(--nt-bg);
    border: 1px solid var(--nt-border-light);
    border-radius: var(--nt-radius-md);
    padding: 16px;
}
.level-card {
    display: flex;
    align-items: flex-start;
    gap: 4px;
    padding: 10px;
    border: 1px solid var(--nt-border-light);
    border-radius: var(--nt-radius-sm);
    margin-bottom: 10px;
    transition: border-color var(--nt-transition);
}
.level-card:hover {
    border-color: var(--nt-border);
}
.level-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.level-columns {
    width: 100%;
}
.level-controls {
    display: flex;
    align-items: center;
    gap: 16px;
}
.negative-switch {
    display: flex;
    align-items: center;
    gap: 6px;
}
.switch-label {
    font-size: 12px;
    color: var(--nt-text-secondary);
}
.level-actions {
    flex-shrink: 0;
}
.button-row {
    display: flex;
    gap: 10px;
    margin-top: 4px;
}
</style>
