// 配置Vue使用Element UI的配置
ELEMENT.locale(ELEMENT.lang.zhCN);

// 配置Axios默认值
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

new Vue({
    el: '#app',
    delimiters: ['[[', ']]'], // 自定义分隔符，避免与Flask的Jinja2模板冲突
    data: {
        // 数据源选项
        dataSourceOptions: {
            engineering: '工程文件',
            manual: '手册',

        },
        // 导入设置
        importSettings: {
            dataSource: 'engineering' // 默认选择工程文件
        },
        // 列标题
        columnHeaders: [],
        // 导入数据
        importData: {
            rows: []
        },
        // 导入预览结果
        importPreview: null,
        // 加载状态
        loading: false
    },
    computed: {
        // 是否可以导入
        canImport() {
            return this.importSettings.dataSource &&
                   this.columnHeaders.length > 0 &&
                   this.importData.rows.length > 0 &&
                   this.hasValidData();
        }
    },
    methods: {
        // 获取列最小宽度
        getColumnMinWidth(column) {
            // 根据列名设置不同的宽度
            const widthMap = {
                '序号': '40',
                '日期': '100',
                '申请时间': '100',
                '问题描述': '300',
                '排故措施': '300',
                '答复详情': '300',
                '标题': '200',
                '版本号': '100',
                '客户期望': '200',
                'ATA': '80',
                '机号/MSN': '120',
                '运营人': '120',
                '服务请求单编号': '150',
                '机型': '100',
                '数据类型': '100',
                '原因和说明': '300',
                '文件名称': '120',
                '分类': '80',
                'MSN有效性': '130',
                '原文文本': '300',
                '飞机序列号/注册号':'100',
                '运营人': '100'
            };
            return widthMap[column] || '150';
        },

        // 获取输入类型
        getInputType(column) {
            return 'text';
        },

        // 获取输入行数
        getInputRows(column) {
            return 1;
        },

        // 加载数据源列
        loadColumns() {
            this.loading = true;
            axios.get('/api/data_source_columns')
                .then(response => {
                    if (response.data.status === 'success') {
                        // 更新数据源选项，确保只显示可用的数据源
                        const availableSources = Object.keys(response.data.columns);

                        // 如果当前选择的数据源不可用，则选择第一个可用的数据源
                        if (!availableSources.includes(this.importSettings.dataSource) && availableSources.length > 0) {
                            this.importSettings.dataSource = availableSources[0];
                        }

                        // 根据选择的数据源更新列标题
                        this.updateColumnHeaders();
                    } else {
                        this.$message.error('加载数据源列失败: ' + response.data.message);
                    }
                })
                .catch(error => {
                    console.error('加载数据源列出错:', error);
                    this.$message.error('加载数据源列时发生错误');
                })
                .finally(() => {
                    this.loading = false;
                });
        },

        // 更新列标题
        updateColumnHeaders() {
            this.loading = true;
            axios.get('/api/data_source_columns')
                .then(response => {
                    if (response.data.status === 'success') {
                        const columns = response.data.columns[this.importSettings.dataSource];
                        if (columns && columns.length > 0) {
                            this.columnHeaders = columns;
                            // 重置导入数据
                            this.resetImportData();
                        } else {
                            this.$message.warning('所选数据源没有可用的列');
                            this.columnHeaders = [];
                        }
                    } else {
                        this.$message.error('获取列失败: ' + response.data.message);
                    }
                })
                .catch(error => {
                    console.error('获取列出错:', error);
                    this.$message.error('获取列时发生错误');
                })
                .finally(() => {
                    this.loading = false;
                });
        },

        // 重置导入数据
        resetImportData() {
            this.importData.rows = [];
            this.importPreview = null;
            // 添加一个空行
            this.addRow();
        },

        // 添加新行
        addRow() {
            const newRow = {};
            this.columnHeaders.forEach(col => {
                newRow[col] = '';
            });
            this.importData.rows.push(newRow);
        },

        // 删除行
        removeRow(rowIndex) {
            this.importData.rows.splice(rowIndex, 1);
            // 如果没有行了，添加一个空行
            if (this.importData.rows.length === 0) {
                this.addRow();
            }
        },

        // 检查是否有有效数据
        hasValidData() {
            return this.importData.rows.some(row => {
                return Object.values(row).some(value => value && value.trim() !== '');
            });
        },

        // 导入预览
        previewImport() {
            if (!this.canImport) {
                this.$message.warning('请先填写数据');
                return;
            }

            this.loading = true;
            const validRows = this.importData.rows.filter(row => {
                return Object.values(row).some(value => value && value.trim() !== '');
            });

            if (validRows.length === 0) {
                this.$message.warning('没有有效数据行');
                this.loading = false;
                return;
            }

            // 发送预览请求
            axios.post(`/api/import/${this.importSettings.dataSource}/preview`, {
                data: validRows,
                dataSource: this.importSettings.dataSource
            })
            .then(response => {
                if (response.data.status === 'success') {
                    // 更新预览数据，包括统计信息和数据内容
                    this.importPreview = {
                        temp_id: response.data.temp_id,  // 确保保存临时文件ID
                        ...response.data.preview,
                        preview_rows: validRows,  // 直接使用过滤后的有效行作为预览数据
                        columns: this.columnHeaders  // 使用当前的列头作为预览列
                    };
                    this.$message.success('预览成功');
                } else {
                    this.$message.error('预览失败: ' + response.data.message);
                }
            })
            .catch(error => {
                console.error('预览出错:', error);
                this.$message.error('预览时发生错误: ' + (error.response ? error.response.data.message : error.message));
            })
            .finally(() => {
                this.loading = false;
            });
        },

        // 确认导入
        confirmImport() {
            if (!this.importPreview) {
                this.$message.warning('请先预览导入');
                return;
            }

            this.loading = true;

            // 发送确认导入请求
            axios.post(`/api/import/${this.importSettings.dataSource}/confirm`, {
                temp_id: this.importPreview.temp_id,
                dataSource: this.importSettings.dataSource
            })
            .then(response => {
                if (response.data.status === 'success') {
                    this.$message.success('导入成功');
                    // 重置数据
                    this.resetImportData();
                } else {
                    this.$message.error('导入失败: ' + response.data.message);
                }
            })
            .catch(error => {
                console.error('导入出错:', error);
                this.$message.error('导入时发生错误: ' + (error.response ? error.response.data.message : error.message));
            })
            .finally(() => {
                this.loading = false;
            });
        },

        cancelImport() {
            this.importPreview = null;
            this.$message({
                message: '已取消导入预览',
                type: 'info'
            });
        }
    },
    created() {
        // 页面创建时加载数据源列
        this.loadColumns();
    },
    watch: {
        // 监听数据源变化
        'importSettings.dataSource': function(newValue) {
            if (newValue) {
                this.updateColumnHeaders();
            }
        }
    }
});
