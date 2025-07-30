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
        },

        getColumnMinWidth(column) {
            if (column === '序号') {
                return '20';
            }
            // 根据列名设置不同的宽度
            const widthMap = {
                '故障发生日期': '100',
                '申请时间': '100',
                '问题描述': '400',
                '答复详情': '400',
                '相似度': '60',
                '机型': '60',
                '数据类型': '100',
                '运营人': '60',
                'ATA': '50',
                '版本号': '60',
                '机号/MSN': '100',
                '原因和说明': '400',
                '原文文本': '400',
                'MSN有效性': '120',
                '文件名称': '120',
                '发布时间': '120',
                '排故措施': '400'
            };
            return widthMap[column] || '120';
        }
    }
});
