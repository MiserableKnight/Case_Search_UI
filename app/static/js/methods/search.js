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
            
            console.log('开始加载初始数据类型');
            await this.loadInitialDataTypes();
            
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
                    throw new Error(`未找到数据源 ${this.defaultSearch.dataSource} 的列信息`);
                }
                
                // 获取列并确保包含"相似度"列
                this.columns = this.dataSourceColumns[this.defaultSearch.dataSource];
                
                // 如果不包含"相似度"列，添加它
                if (!this.columns.includes('相似度')) {
                    this.columns.unshift('相似度'); // 将相似度列添加到最前面
                    console.log('添加相似度列到columns:', this.columns);
                }
                
                // 设置列的可见性
                this.columns.forEach(col => {
                    // 确保相似度列始终可见
                    if (col === '相似度') {
                        this.$set(this.columnVisible, col, true);
                    } else {
                        this.$set(this.columnVisible, col, this.defaultVisibleColumns[this.defaultSearch.dataSource].includes(col));
                    }
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
                
                // 确保包含"相似度"列
                if (!this.columns.includes('相似度')) {
                    this.columns.unshift('相似度');
                    console.log('添加相似度列到columns (错误处理):', this.columns);
                }
                
                this.columns.forEach(col => {
                    // 确保相似度列始终可见
                    if (col === '相似度') {
                        this.$set(this.columnVisible, col, true);
                    } else {
                        this.$set(this.columnVisible, col, true);
                    }
                });
            }
            this.$message.error('获取数据源列名失败：' + error.message);
        }
    },

    async loadInitialDataTypes() {
        try {
            // 从后端API获取当前数据源的可用数据类型
            const response = await fetch(`/api/data_types/${this.defaultSearch.dataSource}`);
            const result = await response.json();
            
            if (result.status === 'success' && result.types) {
                this.availableDataTypes = result.types;
                
                // 如果没有选择任何数据类型，默认全选
                if (!this.defaultSearch.dataTypes.length) {
                    this.defaultSearch.dataTypes = [...this.availableDataTypes];
                } else {
                    // 过滤掉不在可用数据类型中的选项
                    this.defaultSearch.dataTypes = this.defaultSearch.dataTypes.filter(
                        type => this.availableDataTypes.includes(type)
                    );
                }
                
                console.log('数据类型加载成功:', this.availableDataTypes);
            } else {
                throw new Error(result.message || '获取数据类型失败');
            }
        } catch (error) {
            console.error('加载数据类型失败:', error);
            // 如果API调用失败，回退到配置中的静态数据类型
            this.availableDataTypes = CONFIG.dataSourceTypes[this.defaultSearch.dataSource] || [];
            
            if (!this.defaultSearch.dataTypes.length) {
                this.defaultSearch.dataTypes = [...this.availableDataTypes];
            }
            
            this.$message.error('加载数据类型失败：' + error.message);
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
            // 设置加载状态
            this.loading = true;
            
            console.log('开始执行相似度搜索，搜索文本:', this.contentSearch.text);
            console.log('搜索列:', this.contentSearch.selectedColumns);
            console.log('数据源:', this.defaultSearch.dataSource);
            console.log('数据类型:', this.defaultSearch.dataTypes);
            console.log('机型:', this.defaultSearch.aircraftTypes);
            
            // 构建搜索请求数据
            const searchData = {
                data_source: this.defaultSearch.dataSource,
                content: this.contentSearch.text,
                columns: this.contentSearch.selectedColumns,
                data_types: this.defaultSearch.dataTypes,
                aircraft_types: this.defaultSearch.aircraftTypes
            };
            
            console.log('发送相似度搜索请求:', JSON.stringify(searchData));
            
            // 发送搜索请求
            const response = await fetch('/api/similarity_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchData)
            });
            
            console.log('相似度搜索响应状态:', response.status);
            
            const result = await response.json();
            
            console.log('相似度搜索响应结果:', result);
            
            if (result.status === 'success') {
                // 更新搜索结果
                this.searchResults = result.data || [];
                this.total = result.total || 0;
                
                console.log('相似度搜索成功，结果数量:', this.total);
                
                // 确保相似度列在columns中并且可见
                if (!this.columns.includes('相似度')) {
                    this.columns.unshift('相似度');
                    console.log('添加相似度列到columns (搜索结果处理):', this.columns);
                }
                this.$set(this.columnVisible, '相似度', true);
                
                // 计算数据类型统计
                this.calculateTypeStatistics();
                
                // 如果结果为空，不再显示弹窗提示，只依靠页面上的无数据提示区域
            } else {
                // 处理错误
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
            // 无论成功失败，都关闭加载状态
            this.loading = false;
        }
    },

    resetForm() {
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
        await this.loadInitialDataTypes();
        
        // 重置搜索表单
        this.resetForm();
        
        // 执行搜索以更新结果
        await this.handleSearch();
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
    }
}; 