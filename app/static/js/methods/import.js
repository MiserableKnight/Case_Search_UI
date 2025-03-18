const importMethods = {
    showImportDialog() {
        this.importSettings.dataSource = this.defaultSearch.dataSource;
        this.importDialogVisible = true;
    },

    handleBeforeUpload(file) {
        const validTypes = ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        const validExtensions = ['xls', 'xlsx'];

        const extension = file.name.split('.').pop().toLowerCase();
        const isValidType = validTypes.includes(file.type);
        const isValidExtension = validExtensions.includes(extension);

        if (!isValidType && !isValidExtension) {
            this.$message.error('只能上传 Excel 文件（.xlsx 或 .xls 格式）！');
            return false;
        }

        const isLt10M = file.size / 1024 / 1024 < 10;
        if (!isLt10M) {
            this.$message.error('文件大小不能超过 10MB！');
            return false;
        }

        this.importSettings.previewData = null;
        this.importSettings.uploadedFile = file;

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
    }
};
