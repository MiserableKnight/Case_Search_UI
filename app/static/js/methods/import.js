const importMethods = {
    showImportDialog() {
        // 如果当前未选择数据源，则设置为默认数据源 'case'
        if (!this.importSettings.dataSource) {
            this.importSettings.dataSource = 'case';
        }
        this.importDialogVisible = true;
    },

    handleBeforeUpload(file) {
        const isExcel = (
            file.type === 'application/vnd.ms-excel' ||
            file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        );

        if (!isExcel) {
            this.$notify.error({
                title: '文件格式错误',
                message: '请上传 Excel 文件（.xlsx 或 .xls 格式）',
                duration: 3000
            });
            return false;
        }

        if (!this.importSettings.dataSource) {
            this.$notify.error({
                title: '上传失败',
                message: '请先选择数据源',
                duration: 3000
            });
            return false;
        }

        return true;
    },

    handleUploadSuccess(response, file, fileList) {
        if (response.status === 'success') {
            this.importSettings.previewData = {
                original_count: response.data.original_count,
                uploaded_count: response.data.uploaded_count,
                duplicate_count: response.data.duplicate_count,
                new_count: response.data.new_count,
                final_count: response.data.final_count,
                temp_id: response.temp_id
            };
            this.$notify({
                title: '上传成功',
                message: '文件已上传，请确认数据预览',
                type: 'success',
                duration: 3000
            });
        } else {
            let errorMessage = response.message || '未知错误';
            if (response.error_type === 'format_error') {
                errorMessage = '文件格式错误：请检查数据列是否符合要求';
            } else if (response.error_type === 'data_source_mismatch') {
                errorMessage = '数据源不匹配：上传的数据与所选数据源不符';
            } else if (response.error_type === 'missing_columns') {
                errorMessage = '缺少必要的数据列：' + response.missing_columns.join(', ');
            }

            this.$notify.error({
                title: '上传失败',
                message: errorMessage,
                duration: 4000
            });
        }
    },

    handleUploadError(err, file, fileList) {
        let errorMessage = '文件上传失败';

        try {
            const error = JSON.parse(err.message);
            if (error.error_type === 'format_error') {
                errorMessage = '文件格式错误：请检查数据列是否符合要求';
            } else if (error.error_type === 'data_source_mismatch') {
                errorMessage = '数据源不匹配：上传的数据与所选数据源不符';
            } else if (error.message) {
                errorMessage = error.message;
            }
        } catch (e) {
            errorMessage = err.message || errorMessage;
        }

        this.$notify.error({
            title: '上传失败',
            message: errorMessage,
            duration: 4000
        });
    },

    cancelImport() {
        if (this.importSettings.previewData && this.importSettings.previewData.temp_id) {
            fetch(`/api/import/${this.importSettings.dataSource}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    temp_id: this.importSettings.previewData.temp_id
                })
            });
        }
        this.importSettings.previewData = null;
        this.importSettings.uploadedFile = null;
        this.importDialogVisible = false;
    },

    confirmImport() {
        if (!this.importSettings.previewData) {
            this.$message.warning('请先上传文件');
            return;
        }

        this.$confirm('确认要导入这些数据吗？', '确认导入', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        }).then(() => {
            fetch(`/api/import/${this.importSettings.dataSource}/confirm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    temp_id: this.importSettings.previewData.temp_id
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.$notify({
                        title: '导入成功',
                        message: '数据已成功更新',
                        type: 'success',
                        duration: 3000
                    });
                    this.importDialogVisible = false;
                    this.importSettings.previewData = null;
                    this.importSettings.uploadedFile = null;

                    // 导入成功后刷新数据
                    this.$message({
                        message: '正在刷新数据...',
                        type: 'info',
                        duration: 2000
                    });

                    // 使用resetForm方法刷新数据
                    this.resetForm();
                } else {
                    throw new Error(data.message || '导入失败');
                }
            })
            .catch(error => {
                this.$notify.error({
                    title: '导入失败',
                    message: error.message,
                    duration: 4000
                });
            });
        }).catch(() => {});
    },

    // 手动导入相关方法
    showManualImportDialog() {
        console.log('开始显示手动导入对话框');
        console.log('当前数据源:', this.importSettings.dataSource);

        if (!this.importSettings.dataSource) {
            console.log('未选择数据源，显示错误提示');
            this.$notify.error({
                title: '错误',
                message: '请先选择数据源',
                duration: 3000
            });
            return;
        }

        console.log('开始获取数据源对应的列');
        // 获取数据源对应的列
        this.fetchColumnHeaders(this.importSettings.dataSource);
    },

    fetchColumnHeaders(dataSource) {
        console.log('开始获取列信息，数据源:', dataSource);
        this.columnHeaders = [];
        this.manualImportData.rows = [];

        // 显示加载中
        const loading = this.$loading({
            lock: true,
            text: '正在获取数据列...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 0, 0, 0.7)'
        });

        console.log(`开始获取数据源 ${dataSource} 的列信息...`);
        console.log(`API URL: /api/data_columns?source=${dataSource}`);

        // 从后端获取数据源的列信息
        axios.get(`/api/data_columns?source=${dataSource}`)
            .then(response => {
                console.log(`获取到的响应状态:`, response.status);
                console.log(`获取到的响应数据:`, JSON.stringify(response.data));

                if (response.data.success) {
                    this.columnHeaders = response.data.columns;
                    console.log(`成功获取到列:`, this.columnHeaders);
                    // 初始化一行空数据
                    this.addRow();
                    // 显示弹窗
                    this.manualImportDialogVisible = true;
                    console.log('手动导入对话框已显示');
                } else {
                    console.error(`获取列信息失败:`, response.data.message);
                    throw new Error(response.data.message || `获取数据源${dataSource}的列信息失败`);
                }
            })
            .catch(error => {
                console.error(`获取数据源${dataSource}列信息错误:`, error);
                console.error(`错误详情:`, error.response ? JSON.stringify(error.response.data) : '无响应');
                this.$notify.error({
                    title: '获取数据列失败',
                    message: error.message || '无法获取数据列信息',
                    duration: 4000
                });
            })
            .finally(() => {
                loading.close();
                console.log('加载提示已关闭');
            });
    },

    addRow() {
        // 添加一行新的空数据
        const newRow = {};
        this.columnHeaders.forEach(column => {
            newRow[column] = '';
        });
        this.manualImportData.rows.push(newRow);
    },

    removeRow(index) {
        // 删除指定行
        this.manualImportData.rows.splice(index, 1);
    },

    submitManualImport() {
        if (this.manualImportData.rows.length === 0) {
            this.$message.warning('请至少添加一行数据');
            return;
        }

        // 检查必填字段
        let missingFields = false;
        let emptyRows = false;

        this.manualImportData.rows.forEach((row, index) => {
            let allEmpty = true;

            // 检查每一行是否全空
            Object.keys(row).forEach(key => {
                if (row[key] && row[key].trim() !== '') {
                    allEmpty = false;
                }
            });

            if (allEmpty) {
                emptyRows = true;
            }
        });

        if (emptyRows) {
            this.$confirm('存在完全为空的行，是否继续提交？', '确认', {
                confirmButtonText: '继续',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                this.processManualImport();
            }).catch(() => {});
        } else {
            this.processManualImport();
        }
    },

    processManualImport() {
        // 显示加载中
        const loading = this.$loading({
            lock: true,
            text: '正在处理数据...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 0, 0, 0.7)'
        });

        // 发送数据到后端
        fetch(`/api/import/${this.importSettings.dataSource}/manual_import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data: this.manualImportData.rows
            })
        })
        .then(response => response.json())
        .then(data => {
            loading.close();

            if (data.status === 'success') {
                // 设置预览数据
                this.importSettings.previewData = {
                    original_count: data.data.original_count,
                    uploaded_count: data.data.uploaded_count,
                    duplicate_count: data.data.duplicate_count,
                    new_count: data.data.new_count,
                    final_count: data.data.final_count,
                    temp_id: data.temp_id
                };

                this.$notify({
                    title: '导入成功',
                    message: '手动输入的数据已成功处理，请确认数据预览',
                    type: 'success',
                    duration: 3000
                });

                // 关闭手动导入弹窗，显示导入确认弹窗
                this.manualImportDialogVisible = false;

                // 如果导入弹窗已关闭，重新打开
                if (!this.importDialogVisible) {
                    this.importDialogVisible = true;
                }
            } else {
                throw new Error(data.message || '手动导入数据处理失败');
            }
        })
        .catch(error => {
            loading.close();
            this.$notify.error({
                title: '导入失败',
                message: error.message || '处理手动导入数据失败',
                duration: 4000
            });
        });
    },

    // 获取列宽度的配置
    getColumnWidth(column) {
        const widthMap = {
            // 案例数据源
            '故障发生日期': '120px',
            '申请时间': '120px',
            '标题': '200px',
            '版本号': '100px',
            '问题描述': '300px',
            '答复详情': '300px',
            '客户期望': '200px',
            'ATA': '100px',
            '机号/MSN': '120px',
            '运营人': '120px',
            '服务请求单编号': '150px',
            '机型': '100px',
            '数据类型': '100px',

            // 工程文件数据源
            '发布时间': '120px',
            '文件名称': '200px',
            '原因和说明': '300px',
            '文件类型': '100px',
            'MSN有效性': '100px',
            '原文文本': '300px',

            // 手册数据源
            '飞机序列号/注册号/运营人': '200px',

            // 故障报告数据源
            '日期': '120px',
            '排故措施': '300px',
            '飞机序列号': '120px',
            '机号': '100px',

            // 部件拆换记录数据源
            '注册号': '120px',
            '故障描述': '200px',
            '故障现象': '200px',
            '故障原因': '200px',
            '处理结果': '200px',
            '故障件名称': '150px',
            '故障件件号': '150px',
            '故障件序号': '100px',
            '故障ATA章节': '120px',
            '故障MEL': '100px',
            '延期修复': '100px',
            '延期原因': '200px',
            '延期期限': '120px',
            '延期审批人': '120px',
            '备注': '200px'
        };

        return widthMap[column] || '150px'; // 默认宽度
    },

    // 获取输入框类型
    getInputType(column) {
        // 对于长文本字段使用textarea
        const textareaColumns = [
            '问题描述', '答复详情', '客户期望', '原因和说明',
            '原文文本', '排故措施', '故障描述', '故障现象',
            '故障原因', '处理结果', '延期原因', '备注'
        ];

        return textareaColumns.includes(column) ? 'textarea' : 'text';
    },

    // 获取textarea的行数
    getInputRows(column) {
        const rowsMap = {
            '问题描述': 3,
            '答复详情': 3,
            '客户期望': 2,
            '原因和说明': 2,
            '原文文本': 3,
            '排故措施': 3,
            '故障描述': 2,
            '故障现象': 2,
            '故障原因': 2,
            '处理结果': 2,
            '延期原因': 2,
            '备注': 2
        };

        return rowsMap[column] || 1;
    }
};
