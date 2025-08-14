#!/usr/bin/env python3
"""
Excel文件Unicode字符清理工具

用于清理Excel文件中的Unicode控制字符，特别是从右到左标记(U+200F)等字符。
这些字符通常从Excel文件转换过程中产生，会影响数据的正常显示和处理。
"""

import re
import pandas as pd
import argparse
import sys
from pathlib import Path
from typing import Optional, List


def clean_unicode_text(text: str) -> str:
    """
    清理文本中的Unicode控制字符
    
    Args:
        text: 输入文本
        
    Returns:
        清理后的文本
    """
    if pd.isna(text):
        return text
    
    # 常见的双向文本控制字符和零宽度字符
    unicode_control_chars = r'[\u200F\u200E\u202A-\u202E\u2066-\u2069\u061C\u200B\u200C\u200D\uFEFF\u00AD\u034F\u2028\u2029\u202F\u205F\u00A0]'
    
    # 移除控制字符
    cleaned = re.sub(unicode_control_chars, '', str(text))
    
    # 可选：清理其他不可见字符（保留基本的空格、换行等）
    # cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', cleaned)
    
    return cleaned


def clean_excel_file(
    input_file: str, 
    output_file: Optional[str] = None,
    encoding: str = 'utf-8',
    output_encoding: str = 'utf-8-sig'
) -> str:
    """
    清理Excel文件中的Unicode控制字符并转换为CSV
    
    Args:
        input_file: 输入Excel文件路径
        output_file: 输出CSV文件路径（如果为None，则自动生成）
        encoding: 输入文件编码
        output_encoding: 输出文件编码
        
    Returns:
        输出文件路径
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_file}")
    
    # 自动生成输出文件名
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_cleaned.csv"
    
    output_path = Path(output_file)
    
    print(f"正在处理文件: {input_path}")
    print(f"输出编码: {output_encoding}")
    
    try:
        # 读取Excel文件
        print("正在读取Excel文件...")
        df = pd.read_excel(input_path)
        
        original_rows = len(df)
        print(f"原始数据行数: {original_rows}")
        
        # 显示列名
        print(f"列名: {list(df.columns)}")
        
        # 清理列名
        cleaned_columns = [clean_unicode_text(col) for col in df.columns]
        df.columns = cleaned_columns
        
        # 清理每一列
        cleaned_count = 0
        for col in df.columns:
            print(f"正在清理列: {col}")
            
            # 检查该列是否包含需要清理的字符
            has_unicode_chars = df[col].astype(str).str.contains(r'[\u200F\u200E\u202A-\u202E\u2066-\u2069\u061C]', regex=True).any()
            
            if has_unicode_chars:
                print(f"  发现Unicode控制字符，正在清理...")
                original_values = df[col].copy()
                df[col] = df[col].apply(clean_unicode_text)
                
                # 统计被修改的单元格数量
                changed = (original_values.astype(str) != df[col].astype(str)).sum()
                cleaned_count += changed
                print(f"  清理了 {changed} 个单元格")
            else:
                print(f"  未发现需要清理的字符")
        
        # 保存清理后的CSV文件
        print(f"正在保存清理后的文件到: {output_path}")
        df.to_csv(output_path, index=False, encoding=output_encoding)
        
        print(f"\n处理完成!")
        print(f"原始行数: {original_rows}")
        print(f"清理的单元格总数: {cleaned_count}")
        print(f"输出文件: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"处理文件时发生错误: {e}")
        raise


def batch_clean_excel_files(
    input_pattern: str,
    output_dir: Optional[str] = None,
    encoding: str = 'utf-8'
) -> List[str]:
    """
    批量清理Excel文件
    
    Args:
        input_pattern: 输入文件模式（支持通配符）
        output_dir: 输出目录（如果为None，则使用输入文件所在目录）
        encoding: 输入文件编码
        
    Returns:
        处理成功的文件路径列表
    """
    input_path = Path(input_pattern)
    parent_dir = input_path.parent
    
    if output_dir is None:
        output_dir = parent_dir
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找匹配的文件
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(parent_dir.glob(input_path.name))
    
    if not files:
        print(f"未找到匹配的文件: {input_pattern}")
        return []
    
    print(f"找到 {len(files)} 个文件需要处理")
    
    processed_files = []
    for file_path in files:
        try:
            output_file = output_dir / f"{file_path.stem}_cleaned.csv"
            result = clean_excel_file(str(file_path), str(output_file), encoding)
            processed_files.append(result)
        except Exception as e:
            print(f"处理文件 {file_path} 时发生错误: {e}")
    
    print(f"\n批量处理完成! 成功处理了 {len(processed_files)} 个文件")
    return processed_files


def main():
    parser = argparse.ArgumentParser(description='清理Excel文件中的Unicode控制字符')
    parser.add_argument('input', help='输入Excel文件路径或文件模式')
    parser.add_argument('-o', '--output', help='输出CSV文件路径（可选）')
    parser.add_argument('-e', '--encoding', default='utf-8', help='输入文件编码（默认: utf-8）')
    parser.add_argument('--output-encoding', default='utf-8-sig', help='输出文件编码（默认: utf-8-sig）')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--output-dir', help='批量处理时的输出目录')
    
    args = parser.parse_args()
    
    try:
        if args.batch:
            batch_clean_excel_files(args.input, args.output_dir, args.encoding)
        else:
            clean_excel_file(args.input, args.output, args.encoding, args.output_encoding)
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()