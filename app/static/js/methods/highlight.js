// 关键词高亮相关方法
// 将表格单元格文本中命中的搜索关键词以不同颜色高亮（多关键词多色）。
// 关键词来源：this.activeSearchKeywords（computed，收集自所有搜索层级的 keywords）。
const HIGHLIGHT_COLOR_COUNT = 8;

const highlightMethods = {
    /**
     * 转义 HTML 特殊字符，防止单元格内容被当作 HTML 解析（XSS 防护）。
     */
    escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },

    /**
     * 渲染单元格：把命中的关键词包进 <mark> 标签，不同关键词分配不同颜色。
     * 非命中部分仍做 HTML 转义，保证安全。
     * @param {*} value 单元格原始值
     * @returns {string} 可用于 v-html 的 HTML 字符串
     */
    highlightCell(value) {
        const text = (value === null || value === undefined) ? '' : String(value);
        const keywords = this.activeSearchKeywords || [];
        if (!keywords.length) return this.escapeHtml(text);

        // 收集所有关键词在文本中的所有命中区间（不区分大小写）
        const lower = text.toLowerCase();
        const matches = [];
        keywords.forEach((kw, kwIndex) => {
            const kwLower = (kw || '').toLowerCase();
            if (!kwLower) return;
            let pos = 0;
            while ((pos = lower.indexOf(kwLower, pos)) !== -1) {
                matches.push({ start: pos, end: pos + kwLower.length, kwIndex });
                pos += kwLower.length;
            }
        });
        if (!matches.length) return this.escapeHtml(text);

        // 按起始位置升序、长度降序排序，去除重叠区间（保留先出现的较长匹配）
        matches.sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));
        const segments = [];
        let lastEnd = 0;
        for (const m of matches) {
            if (m.start < lastEnd) continue; // 与已选区间重叠，跳过
            segments.push(m);
            lastEnd = m.end;
        }

        // 拼接 HTML：命中部分用带颜色 class 的 <mark> 包裹，其余部分转义
        let html = '';
        let cursor = 0;
        for (const m of segments) {
            html += this.escapeHtml(text.slice(cursor, m.start));
            const colorClass = `kw-hl kw-hl-${m.kwIndex % HIGHLIGHT_COLOR_COUNT}`;
            html += `<mark class="${colorClass}">${this.escapeHtml(text.slice(m.start, m.end))}</mark>`;
            cursor = m.end;
        }
        html += this.escapeHtml(text.slice(cursor));
        return html;
    }
};
