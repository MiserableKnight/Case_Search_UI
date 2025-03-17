import pandas as pd
import os
import logging
from datetime import datetime
from flask import current_app
from pathlib import Path

logger = logging.getLogger(__name__)

class CaseProcessor:
    _instance = None
    _initialized = False
    
    def __new__(cls, file_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, file_path=None):
        # 确保初始化代码只运行一次
        if not self._initialized:
            self.__initialize()
            CaseProcessor._initialized = True
        self.file_path = file_path  # 保存文件路径
    
    def __initialize(self):
        """私有初始化方法"""
        # 只在主进程中打印信息
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            print("敏感词列表读取成功")
            
        # 从应用配置中获取数据路径
        try:
            # 尝试从Flask上下文获取配置
            self.data_path = os.path.join(
                current_app.config['DATA_CONFIG']['data_dir'],
                current_app.config['DATA_SOURCES']['case']
            )
        except Exception as e:
            # 如果不在Flask上下文中，使用默认路径
            print(f"无法从Flask上下文获取配置: {str(e)}")
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(os.path.dirname(app_dir), 'data')
            self.data_path = os.path.join(data_dir, 'raw', 'case.parquet')
            print(f"使用默认数据路径: {self.data_path}")
        
        # 检查并创建数据目录
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        if not os.path.exists(self.data_path):
            logger.warning(f"数据文件不存在: {self.data_path}")
        
        # 初始化其他属性
        self.REQUIRED_COLUMNS = ['类型', '标题', '状态', '技术请求编号', '服务请求单编号', '支持单编号', '版本号', '优先级', 
                               '受理渠道', '申请人', '申请时间', '初始要求答复日期', '协商答复日期', 'SR变更人', '变更原因', 
                               '实际答复时间', '客户名称', 'TR联系人', '联系人电话', '联系人邮箱', '运营人', 'mro', '机型', 
                               '飞机序列号/注册号', '飞机总小时数', '飞机总循环数', '故障发生日期', '故障发生地点', 'ATA', 
                               'CAS信息', 'CMS信息', '维修级别', '问题描述', '客户期望', '答复详情', '答复用时(小时)', 
                               '答复是否超时', 'SR创建人', '创建时间', '答复者', '答复时间', '审批者', '审批时间', '备注信息']
        self.FINAL_COLUMNS = ['故障发生日期', '申请时间', '标题', '版本号', '问题描述', '答复详情', 
                             '客户期望', 'ATA', '机号/MSN', '运营人', '服务请求单编号', '机型', '数据类型']

    # 原始数据必需的列
    REQUIRED_COLUMNS = ['类型', '标题', '状态', '技术请求编号', '服务请求单编号', '支持单编号', '版本号', '优先级', 
                       '受理渠道', '申请人', '申请时间', '初始要求答复日期', '协商答复日期', 'SR变更人', '变更原因', 
                       '实际答复时间', '客户名称', 'TR联系人', '联系人电话', '联系人邮箱', '运营人', 'mro', '机型', 
                       '飞机序列号/注册号', '飞机总小时数', '飞机总循环数', '故障发生日期', '故障发生地点', 'ATA', 
                       'CAS信息', 'CMS信息', '维修级别', '问题描述', '客户期望', '答复详情', '答复用时(小时)', 
                       '答复是否超时', 'SR创建人', '创建时间', '答复者', '答复时间', '审批者', '审批时间', '备注信息']
    
    # 最终需要保留的列
    FINAL_COLUMNS = ['故障发生日期', '申请时间', '标题', '版本号', '问题描述', '答复详情', 
                     '客户期望', 'ATA', '机号/MSN', '运营人', '服务请求单编号', '机型', '数据类型']

    def validate_headers(self, df):
        """验证数据表头是否符合要求"""
        current_columns = set(df.columns)
        required_columns = set(self.REQUIRED_COLUMNS)
        missing_columns = required_columns - current_columns
        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")
        return True

    def clean_data(self, df):
        """清洗数据"""
        # 复制数据框以避免修改原始数据
        cleaned_df = df.copy()
        
        # 清洗日期数据
        def convert_date(date_str):
            try:
                return pd.to_datetime(date_str, format='%Y/%m/%d %H:%M:%S')
            except ValueError:
                try:
                    return pd.to_datetime(date_str, format='%Y/%m/%d %H:%M')
                except ValueError:
                    try:
                        return pd.to_datetime(date_str, format='%Y/%m/%d %H %M')
                    except ValueError:
                        return pd.NaT

        date_columns = ['故障发生日期', '申请时间']
        for col in date_columns:
            cleaned_df[col] = cleaned_df[col].apply(convert_date)
            cleaned_df[col] = cleaned_df[col].dt.strftime('%Y-%m-%d')

        # 清洗机型数据
        cleaned_df['机型'] = cleaned_df['机型'].fillna('无')
        cleaned_df['机型'] = cleaned_df['机型'].str.replace(r'.*ARJ21.*', 'ARJ21', regex=True)
        cleaned_df['机型'] = cleaned_df['机型'].str.replace(r'.*C919.*', 'C919', regex=True)

        # 更新运营人替换规则
        replace_rules = [
            (['天骄', '天骄航空', '天骄航空有限公司'], '天骄'),
            (['东航', '东方航空', '一二三航空', '一二三航空有限公司（东方航空）', '东航技术', 
              '中国东方航空有限公司', '一二三航空有限公司（东航）', '一二三航空有限公司'], '东航'),
            (['江西航', '江西航空有限公司', '江西航空'], '江西航'),
            (['南航', '南方航空', '中国南方航空有限公司'], '南航'),
            (['国航', '中国国航', '中国国际航空股份有限公司'], '国航'),
            (['成航', '成都航空', '成都航空有限公司'], '成航'),
            (['乌航', '乌鲁木齐航空'], '乌航'),
            (['华夏', '华夏航空', '华夏航空股份有限公司'], '华夏'),
            (['金鹏', '金鹏航空'], '金鹏'),
            (['圆通', '圆通货航', '圆通航空'], '圆通'),
            (['中飞通', '中飞通航', '中飞通用航空有限责任公司'], '中飞通'),
            (['中原龙浩', '中原龙浩航空'], '中原龙浩'),
            (['上飞公司维修中心'], '上飞公司维修中心'),
            (['GAMECO', '广州飞机维修工程有限公司（GAMECO）'], 'GAMECO'),
            (['翎亚', '翎亚航空 PT TransNusa Aviation Mandiri', 'TRANSNUSA AVIATION MANDIRI', 'TransNusa'], '翎亚'),
            (['中国商飞', '中国商用飞机有限责任公司'], '中国商飞'),
            (['AMECO', '北京飞机维修工程有限公司'], 'AMECO'),
            (['山东太古', '山东太古飞机工程有限公司'], '山东太古'),
            (['STARCO', '上海科技宇航有限公司 Shanghai Technologies Aerospace (STARCO)'], 'STARCO'),
            (['中飞租', '中国飞机租赁集团控股有限公司'], '中飞租'),
        ]

        # 过滤掉只有单个元素的规则
        filtered_replace_rules = [rule for rule in replace_rules if len(rule[0]) > 1]
        
        # 进行替换操作
        for replacements, target in filtered_replace_rules:
            cleaned_df['运营人'] = cleaned_df['运营人'].replace(replacements, target)
        cleaned_df['运营人'] = cleaned_df['运营人'].fillna('无')

        # 清洗机号数据
        cleaned_df['机号/MSN'] = cleaned_df['飞机序列号/注册号']  # 重命名列
        cleaned_df['机号/MSN'] = cleaned_df['机号/MSN'].str.replace('all', 'ALL', case=True)
        cleaned_df['机号/MSN'] = cleaned_df['机号/MSN'].str.replace('./ALL', 'ALL/ALL', case=True)

        # 清洗ATA数据
        cleaned_df['ATA'] = cleaned_df['ATA'].astype(str)

        # 添加数据类型标记
        cleaned_df['数据类型'] = '服务请求'

        # 删除答复详情为"无"的记录
        cleaned_df = cleaned_df[cleaned_df['答复详情'] != '无']

        # 只保留需要的列
        final_df = cleaned_df[self.FINAL_COLUMNS]
        
        return final_df

    def analyze_changes(self):
        """分析数据变化，但不保存"""
        try:
            # 直接读取Excel文件
            new_data = pd.read_excel(self.file_path)
            
            # 验证表头
            self.validate_headers(new_data)
            
            # 清洗新数据
            cleaned_new_data = self.clean_data(new_data)
            logger.info("新数据清洗完成")
            
            # 读取现有数据
            original_count = 0
            if os.path.exists(self.data_path):
                try:
                    existing_data = pd.read_parquet(self.data_path)
                    original_count = len(existing_data)
                    logger.info(f"现有数据条数: {original_count}")
                except Exception as e:
                    logger.error(f"读取现有数据失败: {str(e)}")
                    existing_data = pd.DataFrame(columns=self.FINAL_COLUMNS)
            else:
                logger.info(f"数据文件不存在，将在保存时创建新文件: {self.data_path}")
                existing_data = pd.DataFrame(columns=self.FINAL_COLUMNS)

            uploaded_count = len(cleaned_new_data)
            logger.info(f"上传文件包含数据: {uploaded_count} 条")

            # 合并数据
            combined_data = pd.concat([cleaned_new_data, existing_data], ignore_index=True)
            
            # 按申请时间倒序排序并去重
            combined_data = combined_data.sort_values('申请时间', ascending=False)
            combined_data = combined_data.drop_duplicates(keep='first')
            final_count = len(combined_data)
            
            # 计算实际新增的数据量
            actual_new_count = final_count - original_count
            logger.info(f"实际新增数据: {actual_new_count} 条")
            
            # 构建预览消息
            message = (
                f"数据变更预览：\n"
                f"原有数据：{original_count} 条\n"
                f"上传数据：{uploaded_count} 条\n"
                f"重复数据：{uploaded_count - actual_new_count} 条\n"
                f"实际新增：{actual_new_count} 条\n"
                f"变更后数据：{final_count} 条\n\n"
                f"是否确认更新数据？"
            )
            
            return True, message, combined_data

        except Exception as e:
            logger.error(f"分析数据时出错: {str(e)}")
            return False, f"数据分析失败: {str(e)}", None

    def save_changes(self, combined_data):
        """保存确认后的数据"""
        try:
            if combined_data is None:
                raise ValueError("没有可保存的数据")

            # 再次确保数据已全字段去重
            combined_data = combined_data.drop_duplicates(keep='first')
            
            # 保存合并后的数据
            combined_data.to_parquet(self.data_path, index=False)
            logger.info("数据更新成功")
            return True, "数据更新成功！"
        except Exception as e:
            logger.error(f"保存数据时出错: {str(e)}")
            return False, f"数据保存失败: {str(e)}"

    @staticmethod
    def validate_columns(columns):
        """验证列名是否有效"""
        if not columns or not isinstance(columns, list):
            return False
        required_fields = {'问题描述', '答复详情'}  # 定义必需字段
        return all(field in columns for field in required_fields)

    def get_columns(self):
        """获取case数据源的所有列"""
        try:
            # 确保正确读取case数据的列信息
            df = pd.read_parquet(self.data_path)
            return df.columns.tolist()
        except Exception as e:
            logger.error(f"读取case数据列名失败: {str(e)}")
            return []

# 确保与上面CaseProcessor类定义之间有至少两个空行
# 删除文件末尾的 process_case_data 函数（该函数导致命名空间污染）

# 在 CaseProcessor 类定义之后（文件末尾）添加以下代码
def load_case_data():
    """加载原始案例数据"""
    data_path = Path(__file__).parent.parent.parent.parent / 'data/raw/case.parquet'
    return pd.read_parquet(data_path)
    
    # 使用 app/__init__.py 中定义的路径
    # input_path = os.path.join(DATA_CONFIG['data_dir'], DATA_SOURCES['case'])
    # output_path = os.path.join(DATA_CONFIG['processed_dir'], 'processed_case.parquet')
    
    # 处理数据的代码
    # ...