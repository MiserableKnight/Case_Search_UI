const importMethods = {
    // 辅助函数：安全解析并清理JSON
    _safeParseJSON(jsonString) {
        try {
            // 处理NaN, Infinity和-Infinity等特殊值
            const cleanedJson = jsonString
                .replace(/:\s*NaN\s*,/g, ': null,')
                .replace(/:\s*NaN\s*}/g, ': null}')
                .replace(/:\s*Infinity\s*,/g, ': null,')
                .replace(/:\s*Infinity\s*}/g, ': null}')
                .replace(/:\s*-Infinity\s*,/g, ': null,')
                .replace(/:\s*-Infinity\s*}/g, ': null}');

            return JSON.parse(cleanedJson);
        } catch (e) {
            console.error('JSON解析失败:', e);
            return null;
        }
    },

    // 辅助函数：清理预览数据中的无效值
    _cleanPreviewData(preview) {
        if (!preview) return null;

        const cleanedPreview = { ...preview };

        // 清理数字字段
        const numericFields = ['original_count', 'uploaded_count', 'duplicate_count', 'new_count', 'final_count'];
        numericFields.forEach(field => {
            if (isNaN(cleanedPreview[field]) || cleanedPreview[field] === null || cleanedPreview[field] === undefined) {
                cleanedPreview[field] = 0;
            }
        });

        // 确保数组字段存在
        if (!Array.isArray(cleanedPreview.preview_rows)) {
            cleanedPreview.preview_rows = [];
        }

        if (!Array.isArray(cleanedPreview.columns)) {
            cleanedPreview.columns = [];
        }

        return cleanedPreview;
    },

    showImportDialog() {
        // 如果当前未选择数据源，则设置为默认数据源 'case'
        if (!this.importSettings.dataSource) {
            this.importSettings.dataSource = 'case';
        }
        this.importDialogVisible = true;
    },

    customUploadRequest(options) {
        // 这是一个完全自定义的上传处理函数
        console.log('启动自定义上传请求', options);

        const { action, file, data, onProgress, onSuccess, onError } = options;

        // 先验证文件
        if (!this.handleBeforeUpload(file)) {
            return;
        }

        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);

        // 添加其他数据
        if (data) {
            Object.keys(data).forEach(key => {
                formData.append(key, data[key]);
            });
        }

        // 创建XMLHttpRequest
        const xhr = new XMLHttpRequest();

        // 进度事件
        if (xhr.upload) {
            xhr.upload.onprogress = event => {
                if (event.total > 0) {
                    event.percent = Math.round(event.loaded * 100 / event.total);
                }
                onProgress(event);
            };
        }

        // 加载完成事件
        xhr.onload = () => {
            if (xhr.status < 200 || xhr.status >= 300) {
                console.error('上传失败', xhr.response);
                return onError(new Error('上传请求失败: ' + xhr.status));
            }

            try {
                // 使用辅助函数安全解析JSON
                const response = this._safeParseJSON(xhr.responseText);

                if (response) {
                    console.log('已安全解析上传响应:', response);

                    // 如果有preview字段，清理其中的数据
                    if (response.preview) {
                        response.preview = this._cleanPreviewData(response.preview);
                    }

                    onSuccess(response);
                } else {
                    throw new Error('响应解析失败');
                }
            } catch (err) {
                console.error('解析上传响应失败:', err, xhr.responseText);

                // 尝试手动提取重要信息
                try {
                    const statusMatch = xhr.responseText.match(/"status"\s*:\s*"([^"]+)"/);
                    const tempIdMatch = xhr.responseText.match(/"temp_id"\s*:\s*"([^"]+)"/);

                    if (statusMatch && statusMatch[1] === 'success' && tempIdMatch) {
                        console.log('手动提取成功，临时ID:', tempIdMatch[1]);

                        // 构造一个最小化的响应对象
                        const minimalResponse = {
                            status: 'success',
                            temp_id: tempIdMatch[1],
                            preview: {
                                original_count: 0,
                                uploaded_count: 0,
                                duplicate_count: 0,
                                new_count: 0,
                                final_count: 0,
                                preview_rows: [],
                                columns: []
                            },
                            message: '成功上传，但数据预览不完整'
                        };

                        // 尝试提取上传的计数
                        const uploadedMatch = xhr.responseText.match(/"uploaded_count"\s*:\s*(\d+)/);
                        if (uploadedMatch) {
                            minimalResponse.preview.uploaded_count = parseInt(uploadedMatch[1], 10) || 0;
                            console.log('成功提取上传计数:', minimalResponse.preview.uploaded_count);
                        }

                        console.log('构造的最小响应:', minimalResponse);
                        return onSuccess(minimalResponse);
                    }
                } catch (extractErr) {
                    console.error('尝试手动提取数据失败:', extractErr);
                }

                onError(new Error('解析响应失败: ' + err.message));
            }
        };

        // 错误事件
        xhr.onerror = e => {
            console.error('上传错误', e);
            onError(e);
        };

        // 超时事件
        xhr.ontimeout = () => {
            console.error('上传超时');
            onError(new Error('上传请求超时'));
        };

        // 开始请求
        xhr.open('POST', action, true);
        xhr.timeout = 60000; // 60秒超时
        xhr.send(formData);

        // 返回上传请求，以便可以中止
        return xhr;
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
        console.log('处理上传成功回调:', response);

        // 响应已经是对象，无需再次解析
        const resp = response;

        // 处理成功响应
        if (resp && resp.status === 'success') {
            let previewData = null;

            // 处理预览数据
            if (resp.preview) {
                // 使用工具函数清理预览数据
                previewData = this._cleanPreviewData(resp.preview);
            } else {
                // 如果没有预览数据，创建一个基本结构
                previewData = {
                    original_count: 0,
                    uploaded_count: 0,
                    duplicate_count: 0,
                    new_count: 0,
                    final_count: 0,
                    preview_rows: [],
                    columns: []
                };
            }

            // 保存预览数据
            this.importSettings.previewData = previewData;

            // 确保temp_id正确保存
            if (resp.temp_id) {
                this.importSettings.previewData.temp_id = resp.temp_id;
            }

            // 显示成功通知
            this.$notify({
                title: '上传成功',
                message: resp.message || '文件已上传，请确认数据预览',
                type: 'success',
                duration: 3000
            });

            // 记录详细信息
            console.log('导入预览数据:', this.importSettings.previewData);
            console.log('临时ID:', resp.temp_id);

            return;
        }

        // 如果响应不成功，显示错误
        console.error('上传成功但响应不成功:', resp);
        this.$notify.error({
            title: '上传失败',
            message: (resp && resp.message) ? resp.message : '未知错误',
            duration: 4000
        });
    },

    handleUploadError(err, file, fileList) {
        console.error('上传错误:', err);

        // 获取错误消息
        let errorMessage = '文件上传失败';

        if (err instanceof Error) {
            // 如果是标准错误对象
            errorMessage = err.message || '上传过程中发生错误';
        } else if (typeof err === 'string') {
            // 如果直接是字符串
            errorMessage = err;
        } else if (err && typeof err === 'object') {
            // 如果是对象
            if (err.message) {
                errorMessage = err.message;
            } else {
                try {
                    errorMessage = JSON.stringify(err);
                } catch (e) {
                    errorMessage = '未知错误';
                }
            }
        }

        console.log('最终错误消息:', errorMessage);

        this.$notify.error({
            title: '上传失败',
            message: errorMessage,
            duration: 4000
        });
    },

    cancelImport() {
        if (this.importSettings.previewData && this.importSettings.previewData.temp_id) {
            console.log('取消导入，临时ID:', this.importSettings.previewData.temp_id);

            fetch(`/api/import/${this.importSettings.dataSource}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    temp_id: this.importSettings.previewData.temp_id
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('取消导入成功:', data);
            })
            .catch(err => {
                console.error('取消导入失败:', err);
                // 不显示错误通知，因为这可能是后台操作
            });
        }
        this.importSettings.previewData = null;
        this.importDialogVisible = false;
    },

    confirmImport() {
        console.log('Starting confirmImport with previewData:', this.importSettings.previewData);

        if (!this.importSettings.previewData || !this.importSettings.previewData.temp_id) {
            this.$message.error('没有可用的导入数据，请先上传文件');
            console.error('Missing previewData or temp_id', this.importSettings);
            return;
        }

        const loading = this.$loading({
            lock: true,
            text: '正在导入数据，请稍候...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 0, 0, 0.7)'
        });

        const requestData = {
            temp_id: this.importSettings.previewData.temp_id,
            dataSource: this.importSettings.dataSource
        };

        console.log('Sending confirmation request with data:', requestData);

        fetch(`/api/import/${this.importSettings.dataSource}/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData),
            timeout: 30000
        })
        .then(response => {
            console.log('Received response:', response);
            if (!response.ok) {
                throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Processed response data:', data);
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
                console.error('Import failed with data:', data);
                this.$notify.error({
                    title: '导入失败',
                    message: data.message || '未知错误',
                    duration: 4000
                });
            }
        })
        .catch(err => {
            console.error('Error during import confirmation:', err);
            loading.close();
            this.$notify.error({
                title: '导入失败',
                message: `网络错误: ${err.message || '请检查网络连接'}`,
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
        // 重新加载数据源信息
        if (this.reloadData) {
            this.reloadData();  // 如果存在reloadData方法则调用
        }
    }
};
