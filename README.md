# 历史问题查询系统

这是一个基于 Flask 和 Vue.js 的历史问题查询系统，支持多关键字搜索、文本相似度计算和 AI 分析功能。

## 功能特点

- 多列关键字搜索
- 文本相似度计算
- AI 智能分析
- 美观的用户界面

## 安装说明

1. 克隆项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置环境变量：
   - 创建 `.env` 文件
   - 添加 DEEPSEEK API 密钥：
     ```
     DEEPSEEK_API_KEY=你的API密钥
     ```
4. 准备数据：
   - 将 parquet 格式的数据文件放在 `app/data` 目录下
   - 默认文件名为 `search_data.parquet`

## 运行说明

1. 启动 Flask 应用：
   ```bash
   python app.py
   ```
2. 在浏览器中访问：`http://localhost:5000`

## 使用说明

1. 在搜索框中输入关键字
2. 点击搜索按钮进行查询
3. 结果将以表格形式展示
4. 可以使用相似度计算功能比较文本
5. 可以使用 AI 分析功能获取智能分析结果

## 技术栈

- 后端：Python + Flask
- 前端：Vue.js + Element UI
- 数据处理：Pandas + NumPy
- 文本分析：scikit-learn + jieba
- AI 集成：DEEPSEEK API 