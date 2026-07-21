<template>
    <el-dialog v-model="visible" title="列显示控制" width="320px">
        <div class="select-all-row">
            <el-checkbox v-model="selectAll" @change="toggleAll">全选</el-checkbox>
        </div>
        <div class="column-list">
            <el-checkbox
                v-for="col in selectableColumns"
                :key="col"
                v-model="tempVisible[col]"
                :label="col"
            >
                {{ col }}
            </el-checkbox>
        </div>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="apply">确定</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useSearchStore } from '../../stores/search'

const visible = defineModel({ type: Boolean, default: false })
const store = useSearchStore()
const tempVisible = reactive({})
const selectAll = ref(false)

// 列显示控制不包含"相似度"（它由相似度搜索自动控制）
const selectableColumns = computed(() => store.columns.filter(col => col !== '相似度'))

watch(visible, val => {
    if (!val) return
    selectableColumns.value.forEach(col => {
        tempVisible[col] = !!store.columnVisible[col]
    })
    selectAll.value = selectableColumns.value.every(col => tempVisible[col])
})

function toggleAll(val) {
    selectableColumns.value.forEach(col => {
        tempVisible[col] = val
    })
}

function apply() {
    const next = { ...store.columnVisible }
    selectableColumns.value.forEach(col => {
        next[col] = !!tempVisible[col]
    })
    store.columnVisible = next
    visible.value = false
}
</script>

<style scoped>
.select-all-row {
    border-bottom: 1px solid var(--nt-border-light);
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.column-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 400px;
    overflow-y: auto;
}
</style>
