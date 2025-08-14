# 脚本工具说明

## CSV/Excel文件Unicode字符清理工具

### 问题描述
CSV和Excel文件中可能包含Unicode控制字符（如U+200F从右到左标记），这些字符通常从Excel文件转换过程中产生，会影响数据的正常显示和处理。

### 解决方案

#### 1. Excel文件清理脚本 `clean_excel_unicode.py`
专门用于清理Excel文件中的Unicode控制字符并转换为CSV格式。

**用法:**
```bash
# 基本用法 - 自动生成输出文件名
python scripts/clean_excel_unicode.py input.xlsx

# 指定输出文件
python scripts/clean_excel_unicode.py input.xlsx -o output.csv

# 指定编码
python scripts/clean_excel_unicode.py input.xlsx -e gbk

# 批量处理Excel文件
python scripts/clean_excel_unicode.py "*.xlsx" --batch

# 批量处理到指定目录
python scripts/clean_excel_unicode.py "*.xlsx" --batch --output-dir cleaned_files/
```

**功能特点:**
- 直接读取Excel文件并输出清洁的CSV
- 自动检测并清理Unicode控制字符
- 支持多种编码格式
- 批量处理多个Excel文件
- 详细的处理日志和统计信息
- 保留原始文件，生成清理后的副本

#### 2. CSV文件清理脚本 `clean_csv_unicode.py`
用于手动清理CSV文件中的Unicode控制字符。

**用法:**
```bash
# 基本用法 - 自动生成输出文件名
python scripts/clean_csv_unicode.py input.csv

# 指定输出文件
python scripts/clean_csv_unicode.py input.csv -o output.csv

# 指定编码
python scripts/clean_csv_unicode.py input.csv -e gbk

# 批量处理
python scripts/clean_csv_unicode.py "*.csv" --batch

# 批量处理到指定目录
python scripts/clean_csv_unicode.py "*.csv" --batch --output-dir cleaned_files/
```

**功能特点:**
- 自动检测并清理Unicode控制字符
- 支持多种编码格式
- 批量处理多个文件
- 详细的处理日志
- 保留原始文件，生成清理后的副本

#### 2. 集成到数据导入系统
在 `app/core/data_processors/data_import_processor.py` 中已集成Unicode字符清理功能。

**功能特点:**
- 自动在数据导入时清理列名和单元格内容
- 支持所有数据源类型
- 统一的清理规则
- 日志记录清理过程

**工作原理:**
1. 导入文件时首先清理列名中的Unicode字符
2. 然后清理所有字符串类型单元格中的Unicode字符
3. 最后执行特定数据源的清洗逻辑

### 支持的Unicode控制字符
- U+200F: 从右到左标记 (RLM)
- U+200E: 从左到右标记 (LRM)
- U+202A-U+202E: 双向嵌入控制字符
- U+2066-U+2069: 双向隔离控制字符
- 其他不可见控制字符

### 使用建议

1. **对于已有文件**: 使用独立脚本进行批量清理
2. **对于新导入**: 使用集成功能自动处理
3. **定期维护**: 可以设置定时任务定期清理数据目录

### 注意事项
- 清理操作会修改原始数据，建议先备份
- 某些特殊用途的控制字符可能需要保留
- 处理前建议先在小样本上测试效果