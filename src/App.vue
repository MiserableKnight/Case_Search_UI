<template>
  <div id="app">
    <!-- Main container -->
    <el-container>
      <!-- Header -->
      <el-header>
        <h1>智能案例查询系统</h1>
      </el-header>

      <!-- Main content -->
      <el-main>
        <!-- Search section -->
        <search-form></search-form>

        <!-- Results section -->
        <results-table :results="store.searchResults" :visible-columns="store.visibleColumns" :loading="store.loading"></results-table>
      </el-main>
    </el-container>

    <!-- Import Dialog -->
    <import-dialog v-if="store.isImportDialogVisible"></import-dialog>
  </div>
</template>

<script>
import { onMounted } from 'vue';
import SearchForm from './components/SearchForm.vue';
import ResultsTable from './components/ResultsTable.vue';
import ImportDialog from './components/ImportDialog.vue'; // Import the dialog
import { useSearchStore } from './store/search';

export default {
  name: 'App',
  components: {
    SearchForm,
    ResultsTable,
    ImportDialog, // Register the dialog
  },
  setup() {
    const store = useSearchStore();

    // Fetch initial column data when the app is mounted
    onMounted(() => {
      store.initialize();
    });

    return { store };
  },
};
</script>

<style>
/* Styles are now imported globally in main.js */
</style>
