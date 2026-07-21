<template>
    <div class="app-shell">
        <header class="app-header">
            <div class="header-inner">
                <h1 class="app-title">历史问题查询系统</h1>
                <nav class="header-nav">
                    <a href="/data_import" class="nav-link">数据导入</a>
                    <a href="/legacy" class="nav-link nav-link--muted">旧版页面</a>
                </nav>
            </div>
        </header>

        <main class="app-main">
            <aside class="sidebar">
                <SearchPanel />
                <SimilarityPanel />
                <SettingsBar />
            </aside>
            <section class="content">
                <ResultTable />
            </section>
        </main>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSearchStore } from './stores/search'
import SearchPanel from './components/SearchPanel.vue'
import SimilarityPanel from './components/SimilarityPanel.vue'
import SettingsBar from './components/SettingsBar.vue'
import ResultTable from './components/ResultTable.vue'

const store = useSearchStore()
onMounted(() => store.init())
</script>

<style scoped>
.app-shell {
    min-height: 100vh;
}
.app-header {
    background: var(--nt-bg);
    border-bottom: 1px solid var(--nt-border-light);
}
.header-inner {
    max-width: 1680px;
    margin: 0 auto;
    padding: 0 24px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.app-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--nt-text);
    margin: 0;
}
.header-nav {
    display: flex;
    gap: 16px;
}
.nav-link {
    font-size: 13px;
    color: var(--nt-text-secondary);
    text-decoration: none;
    transition: color var(--nt-transition);
}
.nav-link:hover {
    color: var(--nt-text);
}
.nav-link--muted {
    color: var(--nt-text-tertiary);
}
.app-main {
    max-width: 1680px;
    margin: 0 auto;
    padding: 20px 24px;
    display: flex;
    gap: 20px;
    align-items: flex-start;
}
.sidebar {
    width: 400px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.content {
    flex: 1;
    min-width: 0;
}
</style>
