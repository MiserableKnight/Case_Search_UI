import axios from 'axios'

// 统一 API 客户端：端点与旧前端完全一致，后端零改动
const client = axios.create({ baseURL: '/', timeout: 300000 })

// 统一提取后端返回的错误消息
export function errorMessage(error, fallback = '请求失败') {
    return error?.response?.data?.message || error?.message || fallback
}

export async function fetchDataSourceColumns() {
    const { data } = await client.get('/api/data_source_columns')
    if (data.status !== 'success') throw new Error(data.message || '获取数据源列名失败')
    return data.columns
}

export async function fetchColumns(source) {
    const { data } = await client.get('/api/data_columns', { params: { source } })
    if (!data.success) throw new Error(data.message || `获取数据源${source}列信息失败`)
    return data.columns
}

// 关键字搜索：payload = { data_source, search_levels, data_types, aircraft_types }
export async function searchCases(payload) {
    const { data } = await client.post('/api/search', payload)
    if (data.status !== 'success') throw new Error(data.message || '搜索失败')
    return data
}

// 相似度搜索：payload = { text, columns, results }
export async function searchSimilarity(payload) {
    const { data } = await client.post('/api/similarity', payload)
    if (data.status !== 'success') throw new Error(data.message || '搜索失败')
    return data
}

// 结果脱敏：payload = { results, fields, dataSource }
export async function anonymizeResults(payload) {
    const { data } = await client.post('/api/anonymize', payload)
    if (data.status !== 'success') throw new Error(data.message || '脱敏处理失败')
    return data.data
}

export async function fetchSensitiveWords() {
    const { data } = await client.get('/api/sensitive_words')
    if (data.status !== 'success') throw new Error(data.message || '获取敏感词列表失败')
    return data.words
}

export async function addSensitiveWord(word, category) {
    const { data } = await client.post('/api/sensitive_words', { word, category })
    if (data.status !== 'success') throw new Error(data.message || '添加敏感词失败')
    return data.message
}

export async function removeSensitiveWord(word, category) {
    const { data } = await client.delete('/api/sensitive_words', { data: { word, category } })
    if (data.status !== 'success') throw new Error(data.message || '删除敏感词失败')
    return data.message
}
