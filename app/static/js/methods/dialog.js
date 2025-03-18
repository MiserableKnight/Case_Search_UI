const dialogMethods = {
    showColumnDialog() {
        this.selectedColumns = this.visibleColumns;

        if (this.defaultSearch.dataSource === 'faults') {
            const essentialColumns = ['日期', '问题描述', '排故措施', '飞机序列号/机号/运营人'];
            essentialColumns.forEach(col => {
                if (this.columns.includes(col) && !this.selectedColumns.includes(col)) {
                    this.selectedColumns.push(col);
                }
            });
        }

        this.columnDialogVisible = true;
    },

    applyColumnSettings() {
        this.columnDialogVisible = false;
        this.columns.forEach(col => {
            this.$set(this.columnVisible, col, this.selectedColumns.includes(col));
        });
    },

    showSearchColumnsDialog() {
        this.searchColumnsDialogVisible = true;
    },

    applySearchColumnSettings() {
        this.searchColumnsDialogVisible = false;
    },

    showDataSourceDialog() {
        this.tempDataSource = this.defaultSearch.dataSource;
        this.dataSourceDialogVisible = true;
    },

    async applyDataSourceSettings() {
        const oldDataSource = this.tempDataSource;
        const newDataSource = this.defaultSearch.dataSource;
        this.dataSourceDialogVisible = false;

        if (oldDataSource !== newDataSource) {
            try {
                await this.updateDataSource(newDataSource);

                // 更新相似度搜索的搜索列为当前数据源的默认搜索列
                this.contentSearch.selectedColumns = [this.defaultSearchColumn[newDataSource]];
                console.log('数据源切换后更新相似度搜索列:', this.contentSearch.selectedColumns);

                this.$notify({
                    title: '成功',
                    message: `数据源已切换至${this.dataSourceOptions[newDataSource]}`,
                    type: 'success',
                    duration: 2000,
                    position: 'top-right'
                });
            } catch (error) {
                this.defaultSearch.dataSource = oldDataSource;
                this.$notify.error({
                    title: '错误',
                    message: '切换数据源失败，已恢复原数据源',
                    duration: 3000,
                    position: 'top-right'
                });
            }
        }
    },

    showAircraftTypesDialog() {
        this.aircraftTypesDialogVisible = true;
    },

    applyAircraftTypesSettings() {
        const oldTypes = [...this.defaultSearch.aircraftTypes];
        this.aircraftTypesDialogVisible = false;

        if (JSON.stringify(oldTypes) !== JSON.stringify(this.defaultSearch.aircraftTypes)) {
            console.log('机型选择已更新:', this.defaultSearch.aircraftTypes);

            // 机型更改后自动执行搜索
            this.handleSearch();

            // 显示通知
            this.$notify({
                title: '成功',
                message: '机型筛选已更新',
                type: 'success',
                duration: 2000,
                position: 'top-right'
            });
        }
    },

    handleSelectAllChange(val) {
        this.selectedColumns = val ? [...this.columns] : [];
    },

    handleSelectedChanged(value) {
        this.selectAll = value.length === this.columns.length;
    },

    handleSelectAllAircraftTypes(val) {
        this.defaultSearch.aircraftTypes = val ? [...CONFIG.aircraftTypeOptions] : [];
    },

    showSensitiveWordDialog() {
        this.loadSensitiveWords();
        this.sensitiveWordDialogVisible = true;
    },

    loadSensitiveWords() {
        console.log('开始加载敏感词列表');
        fetch('/api/sensitive_words')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                console.log('API响应状态:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('API返回的完整数据:', data);
                if (data.status === 'success') {
                    // 确保初始化所有类别的数组
                    this.categories.forEach(category => {
                        if (!this.sensitiveWords[category]) {
                            this.$set(this.sensitiveWords, category, []);
                        }
                    });

                    // 更新敏感词数据
                    if (data.words) {
                        Object.keys(data.words).forEach(category => {
                            this.$set(this.sensitiveWords, category, data.words[category] || []);
                        });
                    }

                    console.log('成功加载敏感词列表:', this.sensitiveWords);
                } else {
                    throw new Error(data.message || '加载失败');
                }
            })
            .catch(error => {
                console.error('加载敏感词失败:', error);
                this.$message.error('加载敏感词失败：' + error.message);

                // 发生错误时也要确保所有类别都被初始化
                this.categories.forEach(category => {
                    if (!this.sensitiveWords[category]) {
                        this.$set(this.sensitiveWords, category, []);
                    }
                });
            });
    },

    addSensitiveWord() {
        if (!this.newWord.trim()) {
            this.$message.warning('请输入敏感词');
            return;
        }

        const word = this.newWord.trim();

        // 检查所有类别中是否已存在该敏感词
        const isWordExists = Object.values(this.sensitiveWords).some(
            categoryWords => categoryWords.some(item => item.word === word)
        );

        if (isWordExists) {
            this.$message.error('该敏感词已存在于词库中');
            return;
        }

        console.log('正在添加敏感词:', {
            word: word,
            category: this.selectedCategory
        });

        fetch('/api/sensitive_words', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                word: word,
                category: this.selectedCategory
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                this.$message.success('敏感词添加成功');
                this.newWord = '';  // 清空输入
                this.loadSensitiveWords();  // 重新加载敏感词列表
            } else {
                throw new Error(data.message || '添加失败');
            }
        })
        .catch(error => {
            console.error('添加敏感词失败:', error);
            this.$message.error('添加敏感词失败：' + error.message);
        });
    },

    removeSensitiveWord(word, category) {
        this.$confirm('确定要删除这个敏感词吗？', '提示', {
            type: 'warning'
        }).then(() => {
            fetch('/api/sensitive_words', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: word,
                    category: category
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.$message.success('删除成功');
                    this.loadSensitiveWords();
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                this.$message.error('删除失败：' + error.message);
            });
        }).catch(() => {});
    }
};
