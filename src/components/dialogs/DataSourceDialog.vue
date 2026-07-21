<template>
    <el-dialog v-model="visible" title="选择数据源" width="320px">
        <el-radio-group v-model="tempSource" class="dialog-list">
            <el-radio
                v-for="(label, value) in store.dataSourceOptions"
                :key="value"
                :value="value"
            >
                {{ label }}
            </el-radio>
        </el-radio-group>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="apply">确定</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSearchStore } from '../../stores/search'

const visible = defineModel({ type: Boolean, default: false })
const store = useSearchStore()
const tempSource = ref(store.dataSource)

watch(visible, val => {
    if (val) tempSource.value = store.dataSource
})

function apply() {
    visible.value = false
    if (tempSource.value !== store.dataSource) {
        store.setDataSource(tempSource.value)
    }
}
</script>

<style scoped>
.dialog-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
</style>
