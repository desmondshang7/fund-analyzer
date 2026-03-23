"""
数据读取与标准化模块
支持：支付宝、微信、银行流水
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re


class DataLoader:
    """多源数据加载器"""
    
    # 数据源特征关键词
    SOURCE_KEYWORDS = {
        'alipay': ['alipay', '支付宝', '13021596499'],
        'wechat': ['wechat', '微信', 'wx', 'tenpay'],
        'bank': ['bank', '银行', '工商银行', '借记卡', '贷记卡']
    }
    
    # 银行特有列名特征
    BANK_COLUMNS = ['借贷标志', '交易摘要', '传票号', '对方户名', '对方账号']
    
    @staticmethod
    def detect_source(filename, df_columns):
        """自动识别数据源类型"""
        filename_lower = filename.lower()
        columns_str = ' '.join(str(col) for col in df_columns).lower()
        
        # 支付宝特征
        if any(k in filename_lower for k in DataLoader.SOURCE_KEYWORDS['alipay']):
            return 'alipay'
        # 微信特征
        elif any(k in filename_lower for k in DataLoader.SOURCE_KEYWORDS['wechat']):
            return 'wechat'
        # 银行特征（通过列名判断）
        elif any(col in columns_str for col in DataLoader.BANK_COLUMNS):
            return 'bank'
        else:
            return 'unknown'
    
    @staticmethod
    def _parse_datetime(series, formats=None):
        """智能解析多种时间格式"""
        if formats is None:
            formats = [
                '%Y%m%d%H%M%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y/%m/%d'
            ]
        
        for fmt in formats:
            try:
                parsed = pd.to_datetime(series, format=fmt, errors='coerce')
                if parsed.notna().sum() > 0:
                    return parsed
            except (ValueError, TypeError):
                continue
        
        # 如果都失败，使用pandas的自动解析
        return pd.to_datetime(series, errors='coerce')
    
    @staticmethod
    def _clean_amount(amount_series):
        """清洗金额数据，处理人民币符号、逗号等"""
        if amount_series.dtype == object:
            # 移除人民币符号、逗号、空格
            cleaned = amount_series.astype(str).str.replace(r'[¥,￥\s]', '', regex=True)
            return pd.to_numeric(cleaned, errors='coerce').abs()
        return pd.to_numeric(amount_series, errors='coerce').abs()
    
    @classmethod
    def load_alipay(cls, df_raw):
        """标准化支付宝数据"""
        df = df_raw.copy()
        
        # 跳过表头行（如果有）
        if df.iloc[0, 0] in ['序号', '交易号']:
            df = df.iloc[1:].reset_index(drop=True)
        
        # 字段映射
        column_map = {
            '交易时间': 'transaction_time',
            '交易金额': 'amount',
            '交易主体的出入账标识': 'direction',
            '交易类型': 'trans_type',
            '收款方的商户名称': 'counterparty',
            '收款方的支付帐号': 'counterparty_id',
            '备注': 'remark',
            '是否涉诈': 'is_fraud',
            '交易订单号': 'order_id',
            '商家订单号': 'merchant_order_id'
        }
        
        # 重命名存在的列
        existing_cols = {k: v for k, v in column_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        # 数据清洗
        df['source'] = '支付宝'
        df['account'] = '13021596499'
        
        # 时间解析
        df['transaction_time'] = cls._parse_datetime(df['transaction_time'])
        
        # 金额处理
        df['amount'] = cls._clean_amount(df['amount'])
        
        # 收支类型标准化
        direction_map = {
            '入账': 'income',
            '出账': 'expense',
            '收入': 'income',
            '支出': 'expense',
            'IN': 'income',
            'OUT': 'expense'
        }
        df['direction'] = df['direction'].map(direction_map).fillna('unknown')
        
        # 涉诈标记
        if 'is_fraud' in df.columns:
            df['is_fraud'] = df['is_fraud'].fillna(False).astype(bool)
        else:
            df['is_fraud'] = False
        
        return df
    
    @classmethod
    def load_bank(cls, df_raw):
        """标准化银行数据"""
        df = df_raw.copy()
        
        # 跳过表头行
        if df.iloc[0, 0] in ['序号', '交易流水号']:
            df = df.iloc[1:].reset_index(drop=True)
        
        # 银行字段映射（工商银行等通用格式）
        column_map = {
            '交易时间': 'transaction_time',
            '金额': 'amount',
            '交易金额': 'amount',
            '借贷标志': 'direction',
            '交易类型': 'trans_type',
            '交易摘要': 'trans_summary',
            '对方账号姓名': 'counterparty',
            '对方户名': 'counterparty',
            '对方账号卡号': 'counterparty_id',
            '对方账号': 'counterparty_id',
            '备注': 'remark',
            '余额': 'balance',
            '账户余额': 'balance',
            '传票号': 'ticket_no',
            '是否涉诈': 'is_fraud'
        }
        
        existing_cols = {k: v for k, v in column_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        df['source'] = '工商银行'
        df['account'] = '6222021605005330530'
        
        # 时间解析
        df['transaction_time'] = cls._parse_datetime(df['transaction_time'])
        
        # 金额处理
        df['amount'] = cls._clean_amount(df['amount'])
        
        # 银行借贷标志：贷=收入，借=支出
        direction_map = {
            '贷': 'income',
            '借': 'expense',
            '收': 'income',
            '付': 'expense',
            'CREDIT': 'income',
            'DEBIT': 'expense',
            '+': 'income',
            '-': 'expense'
        }
        df['direction'] = df['direction'].astype(str).str.strip().map(direction_map).fillna('unknown')
        
        # 涉诈标记
        if 'is_fraud' in df.columns:
            df['is_fraud'] = df['is_fraud'].fillna(False).astype(bool)
        else:
            df['is_fraud'] = False
        
        return df
    
    @classmethod
    def load_wechat(cls, df_raw):
        """标准化微信数据"""
        df = df_raw.copy()
        
        # 跳过表头行
        if df.iloc[0, 0] in ['序号', '交易单号']:
            df = df.iloc[1:].reset_index(drop=True)
        
        # 微信字段映射
        column_map = {
            '交易时间': 'transaction_time',
            '交易发生时间': 'transaction_time',
            '交易金额': 'amount',
            '金额': 'amount',
            '交易主体的出入账标识': 'direction',
            '收支类型': 'direction',
            '交易类型': 'trans_type',
            '交易对方': 'counterparty',
            '收款方的商户名称': 'counterparty',
            '收款方名称': 'counterparty',
            '商户名称': 'counterparty',
            '对方账号': 'counterparty_id',
            '备注': 'remark',
            '交易备注': 'remark',
            '是否涉诈': 'is_fraud'
        }
        
        existing_cols = {k: v for k, v in column_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        df['source'] = '微信'
        df['account'] = 'stf08080118'
        
        # 时间解析
        time_col = df.get('transaction_time')
        if time_col is not None:
            df['transaction_time'] = cls._parse_datetime(time_col)
        
        # 金额处理
        df['amount'] = cls._clean_amount(df['amount'])
        
        # 收支类型标准化
        direction_map = {
            '入账': 'income',
            '出账': 'expense',
            '收入': 'income',
            '支出': 'expense',
            '零钱+': 'income',
            '零钱-': 'expense'
        }
        
        if 'direction' in df.columns:
            df['direction'] = df['direction'].astype(str).str.strip().map(direction_map).fillna('unknown')
        else:
            # 尝试从交易类型推断
            df['direction'] = 'unknown'
        
        # 对手方提取
        df['counterparty'] = df['counterparty'].fillna('未知')
        
        if 'trans_type' not in df.columns:
            df['trans_type'] = '其他'
        
        # 涉诈标记
        if 'is_fraud' in df.columns:
            df['is_fraud'] = df['is_fraud'].fillna(False).astype(bool)
        else:
            df['is_fraud'] = False
        
        return df
    
    @classmethod
    def load_file(cls, file_obj):
        """统一入口：自动识别并加载"""
        # 读取原始数据
        df_raw = pd.read_excel(file_obj)
        
        if df_raw.empty:
            raise ValueError(f"文件 {file_obj.name} 为空")
        
        # 识别类型
        source_type = cls.detect_source(file_obj.name, df_raw.columns)
        
        # 分发处理
        loaders = {
            'alipay': cls.load_alipay,
            'wechat': cls.load_wechat,
            'bank': cls.load_bank,
            'unknown': cls.load_bank  # 默认用银行处理
        }
        
        loader = loaders.get(source_type, cls.load_bank)
        df = loader(df_raw)
        
        # 统一选择核心列
        core_cols = [
            'source', 'account', 'transaction_time', 'amount', 
            'direction', 'trans_type', 'counterparty', 'is_fraud', 
            'remark', 'counterparty_id', 'balance', 'trans_summary'
        ]
        
        # 确保所有列存在
        for col in core_cols:
            if col not in df.columns:
                df[col] = None
        
        # 添加原始文件名
        df['source_file'] = file_obj.name
        
        return df[core_cols + ['source_file']], source_type


# 便捷函数
def merge_multiple_files(uploaded_files):
    """合并多个上传的文件"""
    all_data = []
    file_info = []
    
    for file in uploaded_files:
        try:
            df, source_type = DataLoader.load_file(file)
            all_data.append(df)
            file_info.append({
                'name': file.name,
                'type': source_type,
                'records': len(df)
            })
        except Exception as e:
            file_info.append({
                'name': file.name,
                'type': 'error',
                'error': str(e)
            })
    
    if all_data:
        merged = pd.concat(all_data, ignore_index=True)
        # 按时间排序
        merged = merged.sort_values('transaction_time', ascending=False).reset_index(drop=True)
        return merged, file_info
    else:
        return pd.DataFrame(), file_info


def validate_data(df):
    """数据质量验证"""
    issues = []
    
    # 检查空值
    null_times = df['transaction_time'].isna().sum()
    if null_times > 0:
        issues.append(f"有 {null_times} 条记录时间解析失败")
    
    # 检查异常金额
    zero_amount = (df['amount'] == 0).sum()
    if zero_amount > 0:
        issues.append(f"有 {zero_amount} 条记录金额为0")
    
    negative_amount = (df['amount'] < 0).sum()
    if negative_amount > 0:
        issues.append(f"有 {negative_amount} 条记录金额为负")
    
    # 检查方向未知
    unknown_dir = (df['direction'] == 'unknown').sum()
    if unknown_dir > 0:
        issues.append(f"有 {unknown_dir} 条记录收支方向未知")
    
    return issues
