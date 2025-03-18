// 搜索相关方法
const searchMethods = {
    async initializeData() {
        console.log('开始执行initializeData方法');
        try {
            console.log('开始加载数据源列');
            await this.loadDataSourceColumns();

            // 根据数据源设置默认搜索列
            console.log('设置数据源的默认搜索列');
            this.searchLevels.forEach(level => {
                level.column_name = [this.defaultSearchColumn[this.defaultSearch.dataSource]];
            });

            // 设置相似度搜索的默认搜索列
            this.contentSearch.selectedColumns = [this.defaultSearchColumn[this.defaultSearch.dataSource]];
            console.log('设置相似度搜索的默认搜索列:', this.contentSearch.selectedColumns);

            // 确保机型选择有默认值
            if (!this.defaultSearch.aircraftTypes || this.defaultSearch.aircraftTypes.length === 0) {
                console.log('设置默认机型选择');
                this.defaultSearch.aircraftTypes = ["ARJ21", "无"];
            }

            console.log('initializeData方法执行完成');
        } catch (error) {
            console.error('初始化失败:', error);
            this.$message.error('初始化失败：' + error);
        }
    },

    async loadDataSourceColumns() {
        console.log('开始执行loadDataSourceColumns方法');
        try {
            const response = await fetch('/api/data_source_columns');
            const data = await response.json();
            if (data.status === 'success' && data.columns) {
                this.dataSourceColumns = data.columns;

                if (!this.dataSourceColumns[this.defaultSearch.dataSource]) {
                    console.warn(`未找到数据源 ${this.defaultSearch.dataSource} 的列信息，尝试使用单独的API获取`);
                    // 尝试使用单独的API获取列信息
                    try {
                        const columns = await getDataSourceColumns(this.defaultSearch.dataSource);
                        if (columns && columns.length) {
                            this.columns = columns;
                            // 更新dataSourceColumns
                            this.$set(this.dataSourceColumns, this.defaultSearch.dataSource, columns);
                        } else {
                            throw new Error('获取列信息失败');
                        }
                    } catch (err) {
                        console.error('尝试获取列信息失败:', err);
                        // 使用默认列
                        this.columns = this.defaultVisibleColumns[this.defaultSearch.dataSource] || [];
                    }
                } else {
                    // 获取列
                    this.columns = this.dataSourceColumns[this.defaultSearch.dataSource];
                }

                // 设置列的可见性
                this.columns.forEach(col => {
                    this.$set(this.columnVisible, col, this.defaultVisibleColumns[this.defaultSearch.dataSource].includes(col));
                });

                const defaultColumn = this.defaultSearchColumn[this.defaultSearch.dataSource];
                this.searchLevels.forEach(level => {
                    if (!Array.isArray(level.column_name) || !level.column_name.length) {
                        level.column_name = [defaultColumn];
                    }
                });
            } else {
                throw new Error('获取数据源列名失败：返回数据格式不正确');
            }
        } catch (error) {
            console.error('获取数据源列名失败:', error);
            if (this.defaultVisibleColumns[this.defaultSearch.dataSource]) {
                this.columns = this.defaultVisibleColumns[this.defaultSearch.dataSource];
                this.columns.forEach(col => {
                    this.$set(this.columnVisible, col, true);
                });
            }
            this.$message.error('获取数据源列名失败：' + error.message);
        }
    },

    async handleSearch() {
        // 检查是否有任何搜索条件
        let hasValidSearchCriteria = false;

        // 检查每个搜索级别
        for (const level of this.searchLevels) {
            // 检查关键字是否为空
            if (!level.keywords || !level.keywords.trim()) {
                continue; // 如果关键字为空，检查下一个级别
            }

            // 检查是否选择了搜索列
            if (!level.column_name || !level.column_name.length) {
                continue; // 如果未选择搜索列，检查下一个级别
            }

            // 如果有至少一个有效的搜索条件，标记为有效
            hasValidSearchCriteria = true;
            break;
        }

        // 如果没有有效的搜索条件，提示用户并返回
        if (!hasValidSearchCriteria) {
            this.$message.warning('请输入搜索关键字并选择搜索列');
            return;
        }

        try {
            // 设置加载状态
            this.loading = true;

            // 构建搜索请求数据
            const searchData = {
                data_source: this.defaultSearch.dataSource,
                search_levels: this.searchLevels,
                data_types: this.defaultSearch.dataTypes,
                aircraft_types: this.defaultSearch.aircraftTypes
            };

            // 发送搜索请求
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchData)
            });

            const result = await response.json();

            if (result.status === 'success') {
                // 更新搜索结果
                this.searchResults = result.data || [];
                this.total = result.total || 0;

                // 计算数据类型统计
                this.calculateTypeStatistics();

                // 如果结果为空，不再显示弹窗提示，只依靠页面上的无数据提示区域
            } else {
                // 处理错误
                this.$message.error(result.message || '搜索失败');
                this.searchResults = [];
                this.total = 0;
            }
        } catch (error) {
            console.error('搜索出错:', error);
            this.$message.error('搜索出错: ' + error.message);
            this.searchResults = [];
            this.total = 0;
        } finally {
            // 无论成功失败，都关闭加载状态
            this.loading = false;
        }
    },

    // 计算数据类型统计
    calculateTypeStatistics() {
        if (!this.searchResults.length) {
            this.typeStatistics = {};
            return;
        }

        const stats = {};
        this.searchResults.forEach(item => {
            const type = item['数据类型'] || '未知';
            stats[type] = (stats[type] || 0) + 1;
        });

        this.typeStatistics = stats;
    },

    async handleSimilaritySearch() {
        if (!this.contentSearch.text.trim()) {
            this.$message.warning('请输入要搜索的内容');
            return;
        }

        if (!this.contentSearch.selectedColumns || !this.contentSearch.selectedColumns.length) {
            this.$message.warning('请选择要搜索的列');
            return;
        }

        try {
            this.loading = true;
            console.log('开始相似度搜索，搜索文本:', this.contentSearch.text);
            console.log('搜索列:', this.contentSearch.selectedColumns);

            const response = await fetch('/api/similarity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: this.contentSearch.text,
                    columns: this.contentSearch.selectedColumns,
                    results: this.searchResults.length > 0 ? this.searchResults : null
                })
            });

            console.log('相似度搜索响应状态:', response.status);
            const result = await response.json();
            console.log('相似度搜索响应结果:', result.status);

            if (result.status === 'success') {
                // 更新搜索结果
                this.searchResults = result.data || [];
                this.total = this.searchResults.length;

                console.log('相似度搜索成功，结果数量:', this.total);

                // 只有在有结果且结果中包含相似度列时才添加相似度列
                if (this.searchResults.length > 0 && '相似度' in this.searchResults[0]) {
                    if (!this.columns.includes('相似度')) {
                        this.columns.unshift('相似度');
                        console.log('添加相似度列到columns:', this.columns);
                    }
                    this.$set(this.columnVisible, '相似度', true);
                }

                // 计算数据类型统计
                this.calculateTypeStatistics();

                // 显示成功消息
                this.$message.success('相似度搜索完成');
            } else {
                console.error('相似度搜索失败:', result.message);
                this.$message.error(result.message || '搜索失败');
                this.searchResults = [];
                this.total = 0;
            }
        } catch (error) {
            console.error('相似度搜索出错:', error);
            this.$message.error('相似度搜索出错: ' + error.message);
            this.searchResults = [];
            this.total = 0;
        } finally {
            this.loading = false;
        }
    },

    async resetForm() {
        // 先重置表单
        this.searchLevels = [{
            keywords: '',
            column_name: [this.defaultSearchColumn[this.defaultSearch.dataSource]],
            logic: 'and',
            negative_filtering: false
        }];
        this.contentSearch.text = '';
        this.searchResults = [];
        this.total = 0;
        this.loading = false;
        this.typeStatistics = {};

        // 移除相似度列
        const similarityIndex = this.columns.indexOf('相似度');
        if (similarityIndex !== -1) {
            this.columns.splice(similarityIndex, 1);
            this.$delete(this.columnVisible, '相似度');
        }

        // 刷新数据源数据
        try {
            this.$message({
                message: '正在刷新数据...',
                type: 'info',
                duration: 2000
            });

            // 重新加载数据类型
            await this.loadInitialDataTypes();

            // 重新获取数据源列信息
            await this.getDataSourceColumns();

            this.$message({
                message: '数据刷新成功',
                type: 'success'
            });
        } catch (error) {
            console.error('刷新数据失败:', error);
            this.$message.error('刷新数据失败: ' + error.message);
        }
    },

    addLevel() {
        this.searchLevels.push({
            keywords: '',
            column_name: [this.defaultSearchColumn[this.defaultSearch.dataSource]],
            logic: 'and',
            negative_filtering: false
        });
    },

    removeLevel(index) {
        this.searchLevels.splice(index, 1);
    },

    async updateDataSource(newDataSource) {
        this.defaultSearch.dataSource = newDataSource;

        // 清空之前的数据类型选择
        this.defaultSearch.dataTypes = [];

        // 加载新数据源的列和数据类型
        await this.loadDataSourceColumns();

        // 重置表头和列显示控制
        this.initTableHeaders();

        await this.loadInitialDataTypes();

        // 重置搜索表单
        this.resetForm();
    },

    // 处理搜索列选择变化，包括全选功能
    handleColumnSelectChange(selectedColumns, level) {
        // 检查是否选择了"全选"选项
        const selectAllIndex = selectedColumns.indexOf('__select_all__');

        if (selectAllIndex > -1) {
            // 如果选择了"全选"，则移除"全选"选项
            selectedColumns.splice(selectAllIndex, 1);

            // 获取当前数据源的所有列
            const allColumns = this.dataSourceColumns[this.defaultSearch.dataSource] || [];

            // 判断当前是否已经全选了
            const isAllSelected = level.column_name.length === allColumns.length &&
                                 allColumns.every(col => level.column_name.includes(col));

            if (isAllSelected) {
                // 如果已经全选，则取消全选
                level.column_name = [];
            } else {
                // 否则设置为全选
                level.column_name = [...allColumns];
            }
        } else {
            // 正常设置选中的列
            level.column_name = selectedColumns;
        }
    },

    getDataSourceColumns(source) {
        return new Promise((resolve, reject) => {
            axios.get(`/api/data_columns?source=${source}`)
                .then(response => {
                    if (response.data.success) {
                        resolve(response.data.columns);
                    } else {
                        reject(new Error(response.data.message || `获取数据源${source}的列信息失败`));
                    }
                })
                .catch(error => {
                    console.error(`获取数据源${source}列信息错误:`, error);
                    reject(error);
                });
        });
    },

    performSearch(params) {
        // 重置表头和列显示控制
        this.resetTableDisplay();

        const endpoint = this.searchMode === 'similarity'
            ? '/api/search/similarity'
            : '/api/search';

        axios.post(endpoint, params)
            .then(response => {
                if (response.data.success) {
                    this.searchResults = response.data.results;

                    // 更新表头，确保相似度列只在相似度搜索中显示
                    this.updateTableHeaders(this.searchMode);

                    this.totalResults = response.data.total;
                    this.searchMessage = '';
                } else {
                    this.searchResults = [];
                    this.searchMessage = response.data.message || '搜索失败';
                }
            })
            .catch(error => {
                console.error("搜索错误:", error);
                this.searchResults = [];
                this.searchMessage = '搜索过程中发生错误';
            });
    },

    updateTableHeaders(searchMode) {
        // 根据搜索模式设置表头
        let headers = this.getHeadersForDataSource(this.defaultSearch.dataSource);

        // 只在相似度搜索中添加相似度列
        if (searchMode === 'similarity' && !headers.includes('相似度')) {
            headers.push('相似度');
        } else if (searchMode !== 'similarity') {
            // 在普通搜索中移除相似度列
            headers = headers.filter(h => h !== '相似度');
        }

        this.tableHeaders = headers;
    },

    // 添加获取数据源列信息的方法
    async getDataSourceColumns() {
        try {
            // 使用data.js中定义的getDataSourceColumns函数
            const columns = await getDataSourceColumns(this.defaultSearch.dataSource);
            if (columns && columns.length) {
                // 更新列信息
                this.columns = columns;
                // 更新列可见性
                this.columns.forEach(col => {
                    if (!this.columnVisible.hasOwnProperty(col)) {
                        this.$set(this.columnVisible, col, true);
                    }
                });
                console.log('数据源列信息加载成功:', columns);
                return columns;
            } else {
                throw new Error('未找到数据源列信息');
            }
        } catch (error) {
            console.error('获取数据源列名失败:', error);
            // 如果API调用失败，使用默认列
            if (this.defaultVisibleColumns[this.defaultSearch.dataSource]) {
                this.columns = this.defaultVisibleColumns[this.defaultSearch.dataSource];
                this.columns.forEach(col => {
                    this.$set(this.columnVisible, col, true);
                });
            }
            this.$message.error('获取数据源列名失败：' + error.message);
            throw error;
        }
    },

    // 添加手动刷新数据的方法
    async refreshData() {
        // 直接调用resetForm方法来刷新数据
        await this.resetForm();
    }
};
