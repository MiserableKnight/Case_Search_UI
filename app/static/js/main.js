// 设置Element UI语言
ELEMENT.locale(ELEMENT.lang.zhCN)

// 添加调试日志
console.log('开始初始化Vue实例');
console.log('CONFIG:', CONFIG);
console.log('initialState:', initialState);

// 创建Vue实例
new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            ...CONFIG,  // 首先展开配置
            ...initialState  // 然后展开初始状态
        }
    },
    computed: {
        visibleColumns() {
            if (!this.columns || !this.columnVisible) return [];
            
            // 获取所有可见列
            const visibleCols = this.columns.filter(col => this.columnVisible[col]);
            
            // 如果包含相似度列，确保它在最前面
            if (visibleCols.includes('相似度')) {
                const filteredCols = visibleCols.filter(col => col !== '相似度');
                return ['相似度', ...filteredCols];
            }
            
            return visibleCols;
        },
    },
    created() {
        console.log('Vue实例已创建');
        // 确保在初始化时设置默认值
        if (!this.columns || !this.columns.length) {
            console.log('设置默认列');
            this.columns = this.defaultVisibleColumns[this.defaultSearch.dataSource] || [];
        }
        if (!this.columnVisible) {
            console.log('初始化列可见性');
            this.columnVisible = {};
            this.columns.forEach(col => {
                // 确保相似度列始终可见
                this.$set(this.columnVisible, col, true);
            });
        }
        console.log('调用initializeData方法');
        // 单一初始化方法
        this.initializeApplication();
    },
    methods: {
        ...searchMethods,
        ...tableMethods,
        ...dialogMethods,
        ...importMethods,
        async initializeApplication() {
            try {
                console.log('开始初始化应用...');
                // 调用原始的初始化数据方法
                await this.initializeData();
                
                // 首先加载数据源列信息
                // 注释掉，因为 initializeData 已经做了这个
                
                // 然后初始化表头和列显示控制
                this.initTableHeaders();
                
                // 注释掉，因为 initializeData 已经做了这个
                
                console.log('应用初始化完成');
            } catch (error) {
                console.error("应用初始化失败:", error);
                this.$message.error(`初始化失败: ${error.message}`);
            }
        }
    }
}); 