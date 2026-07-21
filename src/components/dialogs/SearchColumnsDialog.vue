<template>
    <el-dialog v-model="visible" title="搜索范围设置" width="320px">
        <div class="column-list">
            <el-checkbox-group v-model="tempColumns" class="dialog-list">
                <el-checkbox v-for="col in options" :key="col" :value="col">
                    {{ col }}
                </el-checkbox>
            </el-checkbox-group>
        </div>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="apply">确定</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useSearchStore } from '../../stores/search'

const visible = defineModel({ type: Boolean, default: false })
const store = useSearchStore()
const tempColumns = ref([])

const options = computed(() => store.searchableColumns[store.dataSource] || [])

watch(visible, val => {
    if (val) tempColumns.value = [...store.contentSearch.selectedColumns]
})

function apply() {
    store.contentSearch.selectedColumns = [...tempColumns.value]
    visible.value = false
}
</script>

<style scoped>
.column-list {
    max-height: 400px;
    overflow-y: auto;
}
.dialog-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
</style>
