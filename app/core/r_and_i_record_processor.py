import pandas as pd
import os
import logging
from datetime import datetime
from flask import current_app
from pathlib import Path

logger = logging.getLogger(__name__)

class RAndIRecordProcessor:
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
            RAndIRecordProcessor._initialized = True
        self.file_path = file_path  # 保存文件路径
    
    def __initialize(self):
        """私有初始化方法"""
        # 只在主进程中打印信息
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            print("部件拆换记录处理器初始化成功")
            
        # 从应用配置中获取数据路径
        try:
            # 尝试从Flask上下文获取配置
            self.data_path = os.path.join(
                current_app.config['DATA_CONFIG']['data_dir'],
                current_app.config['DATA_SOURCES']['faults']
            )
        except Exception as e:
            # 如果不在Flask上下文中，使用默认路径
            print(f"无法从Flask上下文获取配置: {str(e)}")
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(os.path.dirname(app_dir), 'data')
            self.data_path = os.path.join(data_dir, 'raw', 'faults.parquet')
            print(f"使用默认数据路径: {self.data_path}")
        
        # 检查并创建数据目录
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        if not os.path.exists(self.data_path):
            logger.warning(f"数据文件不存在: {self.data_path}")
        
        # 初始化其他属性
        self.REQUIRED_COLUMNS = ['运营人', '机型', '系列', '飞机序列号', '机号', '拆换日期', 'ATA', '拆卸部件件号', 
                               '拆卸部件序列号', '拆换类型', '拆换原因', '装上部件件号', '装上部件序列号', 
                               '本次使用小时', '本次使用循环', '本次使用天数', '累积使用小时', '累积使用循环', 
                               '累积使用天数', '拆卸部件处理措施']
        self.FINAL_COLUMNS = ['日期', '维修ATA', '问题描述', '排故措施', '运营人', '机型', '飞机序列号', '机号',
                             '数据类型', '拆卸部件件号', '拆卸部件序列号', '装上部件件号', '装上部件序列号']

    # 原始数据必需的列
    REQUIRED_COLUMNS = ['运营人', '机型', '系列', '飞机序列号', '机号', '拆换日期', 'ATA', '拆卸部件件号', 
                       '拆卸部件序列号', '拆换类型', '拆换原因', '装上部件件号', '装上部件序列号', 
                       '本次使用小时', '本次使用循环', '本次使用天数', '累积使用小时', '累积使用循环', 
                       '累积使用天数', '拆卸部件处理措施']
    
    # 最终需要保留的列
    FINAL_COLUMNS = ['日期', '维修ATA', '问题描述', '排故措施', '运营人', '机型', '飞机序列号', '机号',
                     '数据类型', '拆卸部件件号', '拆卸部件序列号', '装上部件件号', '装上部件序列号']

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
                return pd.to_datetime(date_str, format='%Y-%m-%d')
            except ValueError:
                try:
                    return pd.to_datetime(date_str, format='%Y/%m/%d %H:%M:%S')
                except ValueError:
                    try:
                        return pd.to_datetime(date_str, format='%Y/%m/%d %H:%M')
                    except ValueError:
                        try:
                            return pd.to_datetime(date_str, format='%Y/%m/%d')
                        except ValueError:
                            return pd.NaT

        # 处理日期列
        cleaned_df['日期'] = cleaned_df['拆换日期'].apply(convert_date)
        cleaned_df['日期'] = cleaned_df['日期'].dt.strftime('%Y-%m-%d')
        
        # 重命名列
        cleaned_df['维修ATA'] = cleaned_df['ATA']
        cleaned_df['问题描述'] = cleaned_df['拆换原因']
        cleaned_df['排故措施'] = cleaned_df['拆卸部件处理措施']
        
        # 清洗机型数据
        cleaned_df['机型'] = cleaned_df['机型'].fillna('无')
        cleaned_df['机型'] = cleaned_df['机型'].str.replace(r'.*ARJ21.*', 'ARJ21', regex=True)
        cleaned_df['机型'] = cleaned_df['机型'].str.replace(r'.*C919.*', 'C919', regex=True)

        # 更新运营人替换规则
        replace_rules = [
            (['天骄', '天骄航空', '天骄航空有限公司'], '天骄'),
            (['东航', '东方航空', '一二三航空', '一二三航空有限公司（东方航空）', '东航技术', 
              '中国东方航空有限公司', '一二三航空有限公司（东航）', '一二三航空有限公司',
              '中国东方航空集团有限公司'], '东航'),
            (['江西航', '江西航空有限公司', '江西航空'], '江西航'),
            (['南航', '南方航空', '中国南方航空有限公司', '中国南方航空股份有限公司'], '南航'),
            (['国航', '中国国航', '中国国际航空股份有限公司'], '国航'),
            (['成航', '成都航空', '成都航空有限公司'], '成航'),
            (['乌航', '乌鲁木齐航空'], '乌航'),
            (['华夏', '华夏航空', '华夏航空股份有限公司'], '华夏'),
            (['金鹏', '金鹏航空'], '金鹏'),
            (['圆通', '圆通货航', '圆通航空', '杭州圆通货运航空有限公司'], '圆通'),
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

        # 添加数据类型标记
        cleaned_df['数据类型'] = '部件拆换记录'

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
            
            # 按日期倒序排序并去重
            combined_data = combined_data.sort_values('日期', ascending=False)
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
        required_fields = {'问题描述', '排故措施'}  # 定义必需字段
        return all(field in columns for field in required_fields)

    def get_columns(self):
        """获取faults数据源的所有列"""
        try:
            # 确保正确读取faults数据的列信息
            df = pd.read_parquet(self.data_path)
            return df.columns.tolist()
        except Exception as e:
            logger.error(f"读取faults数据列名失败: {str(e)}")
            return []

def load_faults_data():
    """加载故障数据"""
    data_path = Path(__file__).parent.parent.parent.parent / 'data/raw/faults.parquet'
    return pd.read_parquet(data_path)

def load_r_and_i_data():
    """加载部件拆换记录数据"""
    data_path = Path(__file__).parent.parent.parent.parent / 'data/raw/faults.parquet'
    return pd.read_parquet(data_path)