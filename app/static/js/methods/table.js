const tableMethods = {
    getColumnMinWidth(column) {
        if (this.defaultSearch.dataSource === 'case') {
            if (column === '故障发生日期' || column === '申请时间') {
                return '90';
            } else if (column === '问题描述' || column === '答复详情') {
                return '300';
            } else if (column === '相似度') {
                return '70';
            } else if (column === '机型') {
                return '70';
            } else if (column === '数据类型') {
                return '80';
            } else if (column === '机号/MSN' || column === '运营人') {
                return '100';
            }
            return '90';
        }
        
        if (this.defaultSearch.dataSource === 'engineering') {
            if (column === '原因和说明' || column === '原文文本') {
                return '300';
            } else if (column === '相似度') {
                return '70';
            } else if (column === 'MSN有效性' || column === '文件名称' || column === '发布时间') {
                return '90';
            }
            return '60';
        }
        
        if (column === '相似度') {
            return '70';
        } else if (column === '问题描述' || column === '答复详情') {
            return '300';
        } else if (this.importantColumns.includes(column)) {
            return '200';
        }
        return '100';
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

        // 准备要传递的数据
        const analysisData = {
            data: this.selectedRows,
            columns: this.visibleColumns,
            dataSource: this.defaultSearch.dataSource
        };
        
        // 存储数据到localStorage和sessionStorage
        localStorage.setItem('analysisData', JSON.stringify(analysisData));
        sessionStorage.setItem('analysisData', JSON.stringify(analysisData));
        
        // 打开分析页面
        window.open('/analysis', '_blank');
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
    }
}; 