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
            }).catch(err => {
                console.error('取消导入失败:', err);
            });
        }
        this.importSettings.previewData = null;
        this.importDialogVisible = false;
    },

    confirmImport() {
        if (!this.importSettings.previewData || !this.importSettings.previewData.temp_id) {
            this.$message.error('没有可用的导入数据，请先上传文件');
            return;
        }

        const loading = this.$loading({
            lock: true,
            text: '正在导入数据，请稍候...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 0, 0, 0.7)'
        });

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
            loading.close();
            if (data.status === 'success') {
                this.$notify({
                    title: '导入成功',
                    message: `成功导入 ${data.data.new_count} 条数据`,
                    type: 'success',
                    duration: 3000
                });

                // 重新加载数据源信息
                this.loadDataSourceInfo();

                // 关闭导入对话框
                this.importSettings.previewData = null;
                this.importDialogVisible = false;
            } else {
                this.$notify.error({
                    title: '导入失败',
                    message: data.message || '未知错误',
                    duration: 4000
                });
            }
        })
        .catch(err => {
            loading.close();
            console.error('确认导入失败:', err);
            this.$notify.error({
                title: '导入失败',
                message: err.message || '网络错误，请重试',
                duration: 4000
            });
        });
    },

    goToDataImportPage() {
        // 关闭当前对话框
        this.importDialogVisible = false;

        // 跳转到数据导入页面
        window.location.href = '/data_import';
    },

    fetchColumnHeaders(dataSource) {
        if (!dataSource) {
            return Promise.resolve([]);
        }

        // 获取数据源的列头信息
        return fetch('/api/data_source_columns')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.columns && data.columns[dataSource]) {
                    return data.columns[dataSource];
                } else {
                    console.error('获取列头失败:', data.message || '未知错误');
                    return [];
                }
            })
            .catch(err => {
                console.error('获取列头出错:', err);
                return [];
            });
    },

    loadDataSourceInfo() {
        // 重新加载数据类型等信息，用于更新导入后的数据展示
        this.loadDataTypes();
    }
};
