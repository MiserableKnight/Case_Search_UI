<template>
    <el-dialog v-model="visible" title="选择机型" width="320px">
        <div class="select-all-row">
            <el-checkbox v-model="selectAll" @change="toggleAll">全选</el-checkbox>
        </div>
        <el-checkbox-group v-model="tempTypes" class="dialog-list">
            <el-checkbox v-for="type in store.aircraftTypeOptions" :key="type" :value="type">
                {{ type }}
            </el-checkbox>
        </el-checkbox-group>
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
const tempTypes = ref([])

watch(visible, val => {
    if (val) tempTypes.value = [...store.aircraftTypes]
})

const selectAll = computed({
    get: () => tempTypes.value.length === store.aircraftTypeOptions.length,
    set: () => {},
})

function toggleAll(val) {
    tempTypes.value = val ? [...store.aircraftTypeOptions] : []
}

function apply() {
    store.aircraftTypes = [...tempTypes.value]
    visible.value = false
}
</script>

<style scoped>
.select-all-row {
    border-bottom: 1px solid var(--nt-border-light);
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.dialog-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
</style>
