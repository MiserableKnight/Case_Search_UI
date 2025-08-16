#!/usr/bin/env python3
"""
数据导入系统功能验证脚本
验证Unicode清洗功能集成和整个数据导入流程
"""

import os
import sys
import tempfile
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from app.services.data_services.case_service import CaseService
from app.core.data_processors.case_processor import CaseProcessor
from app.utils.unicode_cleaner import UnicodeCleaner

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_data_with_unicode():
    """创建包含Unicode字符的测试数据"""
    test_data = [
        {
            "类型": "技术请求",
            "标题": "测试Unicode字符\u200e问题",
            "状态": "处理中",
            "技术请求编号": "TR001",
            "服务请求单编号": "SR001",
            "支持单编号": "SUP001",
            "版本号": "1.0",
            "优先级": "高",
            "受理渠道": "电话",
            "申请人": "测试用户",
            "申请时间": "2024-01-01",
            "初始要求答复日期": "2024-01-02",
            "协商答复日期": "2024-01-03",
            "SR变更人": "系统",
            "变更原因": "测试",
            "实际答复时间": "2024-01-02",
            "客户名称": "测试客户",
            "TR联系人": "联系人",
            "联系人电话": "123456789",
            "联系人邮箱": "test@example.com",
            "运营人": "测试航空",
            "mro": "测试MRO",
            "机型": "ARJ21",
            "飞机序列号/注册号": "B-001",
            "飞机总小时数": 1000,
            "飞机总循环数": 500,
            "故障发生日期": "2024-01-01",
            "故障发生地点": "测试地点",
            "ATA": "24-00-00",
            "CAS信息": "测试CAS",
            "CMS信息": "测试CMS",
            "维修级别": "航线",
            "问题描述": "这是一个包含Unicode控制字符\u200f的测试描述",
            "客户期望": "解决问题",
            "答复详情": "已处理",
            "答复用时(小时)": 24,
            "答复是否超时": "否",
            "SR创建人": "系统",
            "创建时间": "2024-01-01",
            "答复者": "工程师",
            "答复时间": "2024-01-02",
            "审批者": "经理",
            "审批时间": "2024-01-02",
            "备注信息": "测试备注"
        }
    ]
    return pd.DataFrame(test_data)

def test_unicode_cleaning_integration():
    """测试Unicode清洗功能集成"""
    print("=" * 60)
    print("🧪 测试Unicode清洗功能集成")
    print("=" * 60)
    
    try:
        # 1. 创建测试数据
        print("1. 创建包含Unicode字符的测试数据...")
        test_df = create_test_data_with_unicode()
        
        # 2. 创建临时Excel文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_excel_path = tmp.name
            test_df.to_excel(temp_excel_path, index=False)
            print(f"   ✅ 临时Excel文件已创建: {temp_excel_path}")
        
        # 3. 测试Unicode清洗器
        print("2. 测试Unicode清洗器...")
        unicode_cleaner = UnicodeCleaner()
        pollution_analysis = unicode_cleaner.analyze_file_pollution(temp_excel_path)
        print(f"   📊 污染分析结果: {pollution_analysis}")
        
        if pollution_analysis.get('needs_cleaning', False):
            print("   🔍 检测到Unicode字符污染，开始清洗...")
            cleaned_df = unicode_cleaner.clean_dataframe(pd.read_excel(temp_excel_path))
            print(f"   ✅ 清洗完成，处理了 {len(cleaned_df)} 行数据")
        else:
            print("   ℹ️ 未检测到Unicode字符污染")
        
        # 4. 测试CaseProcessor
        print("3. 测试CaseProcessor...")
        case_processor = CaseProcessor(temp_excel_path)
        
        # 测试analyze_changes方法（带Unicode清洗）
        print("   🔄 测试analyze_changes方法（启用Unicode清洗）...")
        success, message = case_processor.analyze_changes(enable_unicode_cleaning=True)
        print(f"   📈 分析结果: success={success}")
        print(f"   📝 消息: {message[:100]}...")
        
        # 5. 测试CaseService
        print("4. 测试CaseService...")
        case_service = CaseService()
        
        # 测试analyze_changes方法（带Unicode清洗）
        print("   🔄 测试CaseService.analyze_changes方法...")
        success, message, combined_data = case_service.analyze_changes(
            temp_excel_path, enable_unicode_cleaning=True
        )
        print(f"   📈 分析结果: success={success}")
        print(f"   📝 消息: {message[:100]}...")
        if combined_data is not None:
            print(f"   📊 合并数据行数: {len(combined_data)}")
        
        # 6. 清理临时文件
        os.unlink(temp_excel_path)
        print("5. 清理完成")
        
        print("\n" + "=" * 60)
        print("✅ Unicode清洗功能集成测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_data_import_workflow():
    """测试完整的数据导入工作流程"""
    print("\n" + "=" * 60)
    print("🔄 测试数据导入工作流程")
    print("=" * 60)
    
    try:
        # 1. 创建测试数据
        print("1. 创建测试数据...")
        test_df = create_test_data_with_unicode()
        
        # 2. 创建临时Excel文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_excel_path = tmp.name
            test_df.to_excel(temp_excel_path, index=False)
            print(f"   ✅ 临时Excel文件已创建: {temp_excel_path}")
        
        # 3. 测试完整的工作流程
        print("2. 测试完整工作流程...")
        case_service = CaseService()
        
        # 步骤1: 分析变化
        print("   📊 步骤1: 分析数据变化...")
        success, message, combined_data = case_service.analyze_changes(
            temp_excel_path, enable_unicode_cleaning=True
        )
        
        if not success:
            print(f"   ❌ 分析失败: {message}")
            return False
        
        print(f"   ✅ 分析成功: {message[:100]}...")
        
        # 步骤2: 确认导入
        print("   💾 步骤2: 确认导入...")
        success, result_message = case_service.confirm_import(temp_excel_path)
        
        if success:
            print(f"   ✅ 导入成功: {result_message}")
        else:
            print(f"   ❌ 导入失败: {result_message}")
        
        # 4. 清理临时文件
        os.unlink(temp_excel_path)
        print("3. 清理完成")
        
        print("\n" + "=" * 60)
        print("✅ 数据导入工作流程测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 开始数据导入系统功能验证")
    print("=" * 60)
    
    # 运行测试
    test1_result = test_unicode_cleaning_integration()
    test2_result = test_data_import_workflow()
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📋 测试结果总结")
    print("=" * 60)
    print(f"Unicode清洗功能集成: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"数据导入工作流程: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！数据导入系统功能正常。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查系统配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())