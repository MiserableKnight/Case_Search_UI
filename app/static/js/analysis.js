// 初始化Vue实例
new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            tableData: [],
            columns: []
        }
    },
    mounted() {
        this.loadData();
    },
    methods: {
        loadData() {
            try {
                // 尝试从localStorage获取数据
                let storedData = localStorage.getItem('analysisData');
                if (!storedData) {
                    // 如果localStorage没有数据，尝试从sessionStorage获取
                    storedData = sessionStorage.getItem('analysisData');
                }

                if (storedData) {
                    const data = JSON.parse(storedData);
                    this.tableData = data.data || [];
                    this.columns = data.columns || [];
                    this.$message.success(`成功加载 ${this.tableData.length} 条数据`);
                } else {
                    this.$message.warning('没有找到要分析的数据');
                }
            } catch (error) {
                console.error('加载数据失败:', error);
                this.$message.error('数据加载失败: ' + error.message);
            }
        },

        refreshData() {
            this.loadData();
        }
    }
});
