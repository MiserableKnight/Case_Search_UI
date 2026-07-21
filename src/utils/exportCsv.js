// CSV 导出：移植自旧前端 table.js，并修复公式注入（CSV Injection）

/**
 * 单元格净化：
 * 1. 以 = + - @ 开头的内容前置单引号，防止 Excel 按公式执行（公式注入防护）
 * 2. 双引号转义、含逗号/换行/引号时整体加引号（RFC 4180）
 */
function sanitizeCell(value) {
    let s = value === null || value === undefined ? '' : String(value)
    if (/^[=+\-@]/.test(s)) s = `'${s}`
    s = s.replace(/"/g, '""')
    if (s.includes(',') || s.includes('\n') || s.includes('"')) {
        s = `"${s}"`
    }
    return s
}

/**
 * 把选中行按可见列导出为 CSV 并触发下载
 * @param {Array<Object>} rows 选中行
 * @param {string[]} columns 可见列名
 * @returns {number} 导出条数
 */
export function exportRowsToCsv(rows, columns) {
    let csvContent = '﻿' // BOM，保证 Excel 正确识别中文
    csvContent += columns.map(sanitizeCell).join(',') + '\n'

    rows.forEach(row => {
        const rowData = columns.map(col => sanitizeCell(row[col]))
        csvContent += rowData.join(',') + '\n'
    })

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `搜索结果_${new Date().toLocaleString()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)

    return rows.length
}
