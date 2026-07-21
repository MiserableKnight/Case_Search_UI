<template>
    <div class="panel">
        <div class="nt-block-title">搜索设置</div>
        <div class="setting-row">
            <span class="setting-label">数据源</span>
            <span class="nt-chip nt-chip--blue" @click="dataSourceVisible = true">
                {{ store.dataSourceOptions[store.dataSource] }}
            </span>
        </div>
        <div class="setting-row">
            <span class="setting-label">机型</span>
            <span class="nt-chip nt-chip--green" @click="aircraftVisible = true">
                {{ store.aircraftTypes.length ? `已选 ${store.aircraftTypes.length} 项` : '请选择' }}
            </span>
        </div>
        <div class="setting-row">
            <span class="setting-label">敏感词</span>
            <span class="nt-chip nt-chip--orange" @click="sensitiveVisible = true">
                管理敏感词
            </span>
        </div>
        <div class="setting-row">
            <span class="setting-label">数据导入</span>
            <a class="nt-chip nt-chip--purple import-link" href="/data_import">
                前往导入页面
            </a>
        </div>

        <DataSourceDialog v-model="dataSourceVisible" />
        <AircraftTypesDialog v-model="aircraftVisible" />
        <SensitiveWordDialog v-model="sensitiveVisible" />
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSearchStore } from '../stores/search'
import DataSourceDialog from './dialogs/DataSourceDialog.vue'
import AircraftTypesDialog from './dialogs/AircraftTypesDialog.vue'
import SensitiveWordDialog from './dialogs/SensitiveWordDialog.vue'

const store = useSearchStore()
const dataSourceVisible = ref(false)
const aircraftVisible = ref(false)
const sensitiveVisible = ref(false)
</script>

<style scoped>
.panel {
    background: var(--nt-bg);
    border: 1px solid var(--nt-border-light);
    border-radius: var(--nt-radius-md);
    padding: 16px;
}
.setting-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
}
.setting-label {
    font-size: 13px;
    color: var(--nt-text-secondary);
}
.import-link {
    text-decoration: none;
}
</style>
