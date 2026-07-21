<template>
    <el-dialog v-model="visible" title="敏感词管理" width="600px" @open="store.loadSensitiveWords()">
        <div class="add-row">
            <el-input
                v-model="newWord"
                placeholder="输入敏感词"
                style="width: 200px"
                @keyup.enter="addWord"
            />
            <el-select v-model="selectedCategory" style="width: 130px">
                <el-option
                    v-for="cat in categories"
                    :key="cat"
                    :label="categoryLabels[cat]"
                    :value="cat"
                />
            </el-select>
            <el-button type="primary" :disabled="!newWord.trim()" @click="addWord">添加</el-button>
        </div>

        <el-tabs v-model="activeCategory">
            <el-tab-pane
                v-for="cat in categories"
                :key="cat"
                :label="categoryLabels[cat]"
                :name="cat"
            />
        </el-tabs>

        <div class="word-list">
            <div
                v-for="item in currentWords"
                :key="wordText(item)"
                class="word-row"
            >
                <span class="word-text">{{ wordText(item) }}</span>
                <el-button
                    text
                    type="danger"
                    size="small"
                    @click="store.removeSensitiveWord(wordText(item), activeCategory)"
                >
                    删除
                </el-button>
            </div>
            <div v-if="!currentWords.length" class="empty-tip">该分类下暂无敏感词</div>
        </div>
    </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useSearchStore } from '../../stores/search'
import { CATEGORY_LABELS, SENSITIVE_CATEGORIES } from '../../config'

const visible = defineModel({ type: Boolean, default: false })
const store = useSearchStore()

const newWord = ref('')
const selectedCategory = ref('organizations')
const activeCategory = ref('organizations')
const categories = SENSITIVE_CATEGORIES
const categoryLabels = CATEGORY_LABELS

const currentWords = computed(() => store.sensitiveWords[activeCategory.value] || [])

function wordText(item) {
    return typeof item === 'object' && item !== null ? item.word : item
}

async function addWord() {
    const word = newWord.value.trim()
    if (!word) return
    const ok = await store.addSensitiveWord(word, selectedCategory.value)
    if (ok) newWord.value = ''
}
</script>

<style scoped>
.add-row {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 12px;
}
.word-list {
    border: 1px solid var(--nt-border-light);
    border-radius: var(--nt-radius-sm);
    max-height: 280px;
    overflow-y: auto;
}
.word-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px;
    border-bottom: 1px solid var(--nt-border-light);
    font-size: 13px;
}
.word-row:last-child {
    border-bottom: none;
}
.word-row:hover {
    background: var(--nt-bg-hover);
}
.empty-tip {
    padding: 24px;
    text-align: center;
    color: var(--nt-text-tertiary);
    font-size: 13px;
}
</style>
