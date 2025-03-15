const tableMethods = {
    getColumnMinWidth(column) {
        if (column === '序号') {
            return '20';
        }
        if (this.defaultSearch.dataSource === 'case') {
            if (column === '故障发生日期' || column === '申请时间') {
                return '100';
            } else if (column === '问题描述' || column === '答复详情') {
                return '400';
            } else if (column === '相似度') {
                return '60';
            } else if (column === '机型') {
                return '60';
            } else if (column === '数据类型') {
                return '100';
            } else if (column === '运营人') {
                return '60';
            } else if (column === 'ATA') {
                return '50';
            } else if (column === '版本号') {
                return '60';
            } else if (column === '机号/MSN') {
                return '100';
            }
            return '120';
        }
        
        if (this.defaultSearch.dataSource === 'engineering') {
            if (column === '原因和说明' || column === '原文文本') {
                return '400';
            } else if (column === '相似度') {
                return '80';
            } else if (column === 'MSN有效性' || column === '文件名称' || column === '发布时间') {
                return '120';
            }
            return '100';
        }

        if (this.defaultSearch.dataSource === 'faults') {
            if (column === '问题描述' || column === '排故措施') {
                return '400';
            } else if (column === '相似度') {
                return '80';
            } 
            return '100';
        }
        
        if (column === '相似度') {
            return '80';
        } else if (column === '问题描述' || column === '答复详情') {
            return '400';
        } else if (this.importantColumns.includes(column)) {
            return '250';
        }
        return '150';
    },

    getColumnFixedWidth(column) {
        // ... 列宽度计算方法
    },

    handleSelectionChange(selection) {
        this.selectedRows = selection;
    },

    handleRowClick(row, column, event) {
        // 如果点击的是选择框列，不做额外处理
        if (column.type === 'selection') {
            return;
        }
        
        // 获取表格引用
        const table = this.$refs.dataTable;
        
        // 如果按住Shift键
        if (event.shiftKey && this.lastClickedRow) {
            // 找到当前行和上次点击行的索引
            const currentIndex = this.searchResults.indexOf(row);
            const lastIndex = this.searchResults.indexOf(this.lastClickedRow);
            
            // 确定范围的起始和结束索引
            const startIndex = Math.min(currentIndex, lastIndex);
            const endIndex = Math.max(currentIndex, lastIndex);
            
            // 选择范围内的所有行
            for (let i = startIndex; i <= endIndex; i++) {
                table.toggleRowSelection(this.searchResults[i], true);
            }
        } else {
            // 普通点击，切换当前行的选择状态
            table.toggleRowSelection(row);
        }
        
        // 记录最后点击的行，用于Shift+点击功能
        this.lastClickedRow = row;
    },

    getRowClass({ row }) {
        return this.selectedRows.includes(row) ? 'selected-row' : '';
    },

    analyzeSelectedData() {
        if (!this.selectedRows.length) {
            this.$message.warning('请先选择要分析的数据');
            return;
        }

        if (this.selectedRows.length > 300) {
            this.$message.warning('为确保分析页面性能，建议选择不超过300条数据');
            return;
        }

        // 准备要传递的数据
        const analysisData = {
            data: this.selectedRows,
            columns: this.visibleColumns,
            dataSource: this.defaultSearch.dataSource
        };
        
        try {
            console.log('准备传递的数据:', analysisData);
            console.log('数据大小:', JSON.stringify(analysisData).length, 'bytes');
            
            // 存储数据到localStorage和sessionStorage
            localStorage.setItem('analysisData', JSON.stringify(analysisData));
            sessionStorage.setItem('analysisData', JSON.stringify(analysisData));
            
            console.log('数据已成功存储到localStorage和sessionStorage');
            
            // 打开分析页面
            window.open('/analysis', '_blank');
        } catch (error) {
            console.error('数据存储失败:', error);
            this.$message.error('数据传递失败: ' + error.message);
        }
    },

    anonymizeResults() {
        try {
            if (!this.searchResults.length) {
                this.$message.warning('没有可脱敏的搜索结果');
                return;
            }
            
            // 根据数据源确定需要脱敏的字段
            let fieldsToAnonymize;
            if (this.defaultSearch.dataSource === 'engineering') {
                fieldsToAnonymize = ['原因和说明', '原文文本', '文件名称'];
            } else if (this.defaultSearch.dataSource === 'faults') {
                fieldsToAnonymize = ['问题描述', '排故措施'];
            } else {
                fieldsToAnonymize = ['标题', '问题描述', '答复详情', '客户期望', '机号/MSN', '运营人'];
            }
            
            fetch('/api/anonymize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    results: this.searchResults,
                    fields: fieldsToAnonymize,
                    dataSource: this.defaultSearch.dataSource
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.searchResults = data.data;
                    this.$message.success('脱敏处理完成');
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                this.$message.error('脱敏处理失败：' + error.message);
            });
        } catch (error) {
            this.$message.error('脱敏处理失败：' + error.message);
        }
    },

    exportToCsv() {
        if (!this.selectedRows.length) {
            this.$message.warning('请先选择要导出的数据');
            return;
        }
        
        const visibleCols = this.visibleColumns;
        
        let csvContent = '\uFEFF';  // 添加BOM标记以支持中文
        
        // 添加表头
        csvContent += visibleCols.join(',') + '\n';
        
        // 只导出选中的行
        this.selectedRows.forEach(row => {
            const rowData = visibleCols.map(col => {
                let cellData = row[col] || '';
                // 处理单元格数据，确保CSV格式正确
                cellData = cellData.toString().replace(/"/g, '""');
                if (cellData.includes(',') || cellData.includes('\n') || cellData.includes('"')) {
                    cellData = `"${cellData}"`;
                }
                return cellData;
            });
            csvContent += rowData.join(',') + '\n';
        });
        
        // 创建并下载文件
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `搜索结果_${new Date().toLocaleString()}.csv`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.$message.success(`成功导出 ${this.selectedRows.length} 条记录`);
    },
    
    // 检查选中的行数据
    checkSelectedRows() {
        if (!this.selectedRows.length) {
            this.$message.warning('没有选中的行');
            return;
        }
        
        console.log('选中的行数量:', this.selectedRows.length);
        console.log('选中的行数据:', this.selectedRows);
        
        // 测试localStorage存储
        try {
            const testData = {
                data: this.selectedRows,
                columns: this.visibleColumns,
                dataSource: this.defaultSearch.dataSource
            };
            
            const jsonString = JSON.stringify(testData);
            console.log('JSON字符串长度:', jsonString.length);
            
            // 尝试存储到localStorage
            localStorage.setItem('testData', jsonString);
            console.log('测试数据已存储到localStorage');
            
            // 读取并验证
            const storedData = JSON.parse(localStorage.getItem('testData'));
            console.log('从localStorage读取的测试数据:', storedData);
            
            // 清理测试数据
            localStorage.removeItem('testData');
            
            this.$message.success(`已选中 ${this.selectedRows.length} 行数据，详情请查看控制台`);
        } catch (error) {
            console.error('测试localStorage存储时出错:', error);
            this.$message.error('测试数据存储失败: ' + error.message);
        }
    },

    initTableHeaders() {
        // 修复这里的问题：确保不会错误地添加"相似度"列到普通搜索结果中
        let headers = [];
        
        // 根据当前数据源设置表头
        if (this.defaultSearch.dataSource) {
            try {
                headers = this.getHeadersForDataSource(this.defaultSearch.dataSource);
                
                // 只有在相似度搜索模式下才添加相似度列
                if (this.searchMode === 'similarity' && !headers.includes('相似度')) {
                    headers.push('相似度');
                }
            } catch (error) {
                console.error("获取表头失败:", error);
                // 使用默认表头
                headers = this.getDefaultHeaders(this.defaultSearch.dataSource);
            }
        }
        
        // 更新表头
        this.tableHeaders = headers;
        
        // 确保列显示控制内容不会被错误修改
        this.updateColumnDisplayControls();
    },

    updateColumnDisplayControls() {
        // 修复列显示控制的内容，确保它独立于当前表头
        // 从原始数据源获取完整的列列表，而不是使用当前表头
        this.getDataSourceColumns(this.defaultSearch.dataSource)
            .then(columns => {
                // 生成列显示控制项，不包含相似度列
                this.columnControls = columns.map(col => {
                    return {
                        name: col,
                        visible: this.tableHeaders.includes(col)
                    };
                });
            })
            .catch(error => {
                console.error("获取列显示控制内容失败:", error);
            });
    },

    getDefaultHeaders(dataSource) {
        // 根据数据源返回默认表头
        const defaultHeaders = {
            'case': ['序号', '故障发生日期', '申请时间', '标题', '版本号', '问题描述', '答复详情', 
                    '客户期望', 'ATA', '机号/MSN', '运营人', '服务请求单编号', '机型', '数据类型'],
            'engineering': ['序号', '发布时间', '文件名称', '原因和说明', '文件类型', 'MSN有效性', 
                           '原文文本', '机型', '数据类型'],
            'manual': ['序号', '申请时间', '问题描述', '答复详情', '飞机序列号/注册号/运营人',
                      '机型', '数据类型'],
            'faults': ['序号', '日期', '问题描述', '排故措施', '运营人', '飞机序列号', '机号',
                      '机型', '数据类型']
        };
        
        return defaultHeaders[dataSource] || [];
    },

    getHeadersForDataSource(dataSource) {
        // 尝试从数据源列配置中获取表头
        if (this.dataSourceColumns && this.dataSourceColumns[dataSource]) {
            // 添加序号列
            if (!this.dataSourceColumns[dataSource].includes('序号')) {
                return ['序号', ...this.dataSourceColumns[dataSource]];
            }
            return [...this.dataSourceColumns[dataSource]];
        }
        
        // 如果无法获取，则返回默认表头
        return this.getDefaultHeaders(dataSource);
    },

    resetTableDisplay() {
        // 重置表头和列显示控制
        this.searchResults = [];
        this.searchMessage = '';
        this.initTableHeaders(); // 重新初始化表头
    }
}; 