// 关键词高亮：移植自旧前端 highlight.js
// 所有片段（命中与未命中）都做 HTML 转义，保证 v-html 使用安全

export function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
}

export const HIGHLIGHT_COLOR_COUNT = 6

/**
 * 把命中关键词的部分包进 <mark>，不同关键词分配不同柔和底色。
 * @param {*} value 单元格原始值
 * @param {string[]} keywords 关键词列表
 * @returns {string} 可用于 v-html 的安全 HTML
 */
export function highlightCell(value, keywords) {
    const text = value === null || value === undefined ? '' : String(value)
    if (!keywords || !keywords.length) return escapeHtml(text)

    // 收集所有关键词在文本中的所有命中区间（不区分大小写）
    const lower = text.toLowerCase()
    const matches = []
    keywords.forEach((kw, kwIndex) => {
        const kwLower = (kw || '').toLowerCase()
        if (!kwLower) return
        let pos = 0
        while ((pos = lower.indexOf(kwLower, pos)) !== -1) {
            matches.push({ start: pos, end: pos + kwLower.length, kwIndex })
            pos += kwLower.length
        }
    })
    if (!matches.length) return escapeHtml(text)

    // 按起始位置升序、长度降序排序，去除重叠区间（保留先出现的较长匹配）
    matches.sort((a, b) => a.start - b.start || b.end - b.start - (a.end - a.start))
    const segments = []
    let lastEnd = 0
    for (const m of matches) {
        if (m.start < lastEnd) continue
        segments.push(m)
        lastEnd = m.end
    }

    // 拼接 HTML：命中部分用带颜色 class 的 <mark> 包裹，其余部分转义
    let html = ''
    let cursor = 0
    for (const m of segments) {
        html += escapeHtml(text.slice(cursor, m.start))
        const colorClass = `kw-hl kw-hl-${m.kwIndex % HIGHLIGHT_COLOR_COUNT}`
        html += `<mark class="${colorClass}">${escapeHtml(text.slice(m.start, m.end))}</mark>`
        cursor = m.end
    }
    html += escapeHtml(text.slice(cursor))
    return html
}
