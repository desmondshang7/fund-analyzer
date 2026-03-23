"""
资金分析核心算法
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class FundAnalyzer:
    """资金分析器"""
    
    def __init__(self, df):
        """
        初始化分析器
        
        Args:
            df: DataFrame，包含标准化后的交易数据
        """
        if df.empty:
            raise ValueError("数据为空，无法进行分枧")
        
        self.df = df.copy()
        
        # 确保时间列为 datetime 类型
        self.df['transaction_time'] = pd.to_datetime(self.df['transaction_time'], errors='coerce')
        self.df['date'] = self.df['transaction_time'].dt.date
        self.df['hour'] = self.df['transaction_time'].dt.hour
        self.df['month'] = self.df['transaction_time'].dt.to_period('M')
        self.df['weekday'] = self.df['transaction_time'].dt.weekday  # 0=周一
        
        # 确保金额数值类型
        self.df['amount'] = pd.to_numeric(self.df['amount'], errors='coerce')
        
        # 缓存计算结果
        self._income_df = None
        self._expense_df = None
        self._fraud_df = None
    
    @property
    def income_df(self):
        """收入数据缓存"""
        if self._income_df is None:
            self._income_df = self.df[self.df['direction'] == 'income']
        return self._income_df
    
    @property
    def expense_df(self):
        """支出数据缓存"""
        if self._expense_df is None:
            self._expense_df = self.df[self.df['direction'] == 'expense']
        return self._expense_df
    
    @property
    def fraud_df(self):
        """涉诈数据缓存"""
        if self._fraud_df is None:
            self._fraud_df = self.df[self.df['is_fraud'] == True]
        return self._fraud_df
    
    # ==================== 基础统计 ====================
    
    def basic_stats(self):
        """基础统计信息"""
        income = self.income_df['amount'].sum()
        expense = self.expense_df['amount'].sum()
        
        # 处理可能的 NaN
        income = income if pd.notna(income) else 0
        expense = expense if pd.notna(expense) else 0
        
        # 计算日期范围
        valid_times = self.df['transaction_time'].dropna()
        date_range = {
            'start': valid_times.min() if len(valid_times) > 0 else None,
            'end': valid_times.max() if len(valid_times) > 0 else None
        }
        
        # 计算天数
        days = (date_range['end'] - date_range['start']).days + 1 if date_range['start'] and date_range['end'] else 0
        
        return {
            'total_records': len(self.df),
            'valid_records': len(self.df.dropna(subset=['transaction_time', 'amount'])),
            'date_range': date_range,
            'days_span': days,
            'total_income': income,
            'total_expense': expense,
            'net_flow': income - expense,
            'avg_daily_income': income / days if days > 0 else 0,
            'avg_daily_expense': expense / days if days > 0 else 0,
            'fraud_count': int(self.df['is_fraud'].sum()),
            'fraud_amount': float(self.fraud_df['amount'].sum()) if len(self.fraud_df) > 0 else 0,
            'fraud_ratio': float(self.df['is_fraud'].mean() * 100),
            'sources': self.df['source'].value_counts().to_dict(),
            'accounts': self.df['account'].nunique()
        }
    
    # ==================== 时间分析 ====================
    
    def daily_trend(self, fill_missing=True):
        """
        日趋势分析
        
        Args:
            fill_missing: 是否填充缺失日期
        """
        daily = self.df.groupby(['date', 'direction'])['amount'].sum().reset_index()
        daily_pivot = daily.pivot(index='date', columns='direction', values='amount').fillna(0)
        
        # 确保 income 和 expense 列都存在
        for col in ['income', 'expense', 'unknown']:
            if col not in daily_pivot.columns:
                daily_pivot[col] = 0
        
        daily_pivot = daily_pivot.reset_index()
        daily_pivot['net'] = daily_pivot['income'] - daily_pivot['expense']
        
        # 填充缺失日期
        if fill_missing and len(daily_pivot) > 0:
            date_range = pd.date_range(
                start=daily_pivot['date'].min(),
                end=daily_pivot['date'].max(),
                freq='D'
            )
            daily_pivot = daily_pivot.set_index('date').reindex(date_range, fill_value=0).reset_index()
            daily_pivot = daily_pivot.rename(columns={'index': 'date'})
        
        return daily_pivot
    
    def hourly_distribution(self):
        """时段分布"""
        hourly = self.df.groupby(['hour', 'direction']).agg({
            'amount': ['sum', 'count']
        }).reset_index()
        hourly.columns = ['hour', 'direction', 'amount_sum', 'count']
        return hourly
    
    def weekday_distribution(self):
        """星期分布"""
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        weekday = self.df.groupby(['weekday', 'direction']).agg({
            'amount': ['sum', 'count']
        }).reset_index()
        weekday.columns = ['weekday', 'direction', 'amount_sum', 'count']
        weekday['weekday_name'] = weekday['weekday'].map(lambda x: weekday_names[x])
        
        return weekday
    
    def monthly_trend(self):
        """月度趋势"""
        monthly = self.df.groupby(['month', 'direction'])['amount'].sum().reset_index()
        monthly_pivot = monthly.pivot(index='month', columns='direction', values='amount').fillna(0)
        
        for col in ['income', 'expense', 'unknown']:
            if col not in monthly_pivot.columns:
                monthly_pivot[col] = 0
        
        monthly_pivot = monthly_pivot.reset_index()
        monthly_pivot['net'] = monthly_pivot['income'] - monthly_pivot['expense']
        monthly_pivot['month_str'] = monthly_pivot['month'].astype(str)
        
        return monthly_pivot
    
    def detect_night_transactions(self, night_start=22, night_end=6):
        """
        检测夜间交易
        
        Args:
            night_start: 夜间开始时间（小时）
            night_end: 夜间结束时间（小时）
        """
        night_mask = (self.df['hour'] >= night_start) | (self.df['hour'] <= night_end)
        night_df = self.df[night_mask].copy()
        
        fraud_count = int(night_df['is_fraud'].sum())
        
        return {
            'count': len(night_df),
            'amount': float(night_df['amount'].sum()),
            'fraud_count': fraud_count,
            'fraud_ratio': fraud_count / len(night_df) * 100 if len(night_df) > 0 else 0,
            'percentage_of_total': len(night_df) / len(self.df) * 100,
            'details': night_df
        }
    
    # ==================== 对手方分析 ====================
    
    def counterparty_analysis(self, direction='expense', top_n=10, min_count=1):
        """
        对手方分析
        
        Args:
            direction: 'expense' 或 'income'
            top_n: 返回前 N 个对手方
            min_count: 最少交易次数过滤
        """
        df_dir = self.df[self.df['direction'] == direction].copy()
        
        if len(df_dir) == 0:
            return pd.DataFrame()
        
        stats = df_dir.groupby('counterparty').agg({
            'amount': ['count', 'sum', 'mean', 'max', 'min'],
            'is_fraud': 'sum',
            'transaction_time': ['min', 'max']
        }).reset_index()
        
        stats.columns = [
            'counterparty', 'trans_count', 'total_amount', 'avg_amount',
            'max_amount', 'min_amount', 'fraud_count', 'first_time', 'last_time'
        ]
        
        # 过滤最少交易次数
        stats = stats[stats['trans_count'] >= min_count]
        
        # 计算占比
        total_amount = df_dir['amount'].sum()
        stats['percentage'] = stats['total_amount'] / total_amount * 100
        
        # 计算时间跨度（天）
        stats['time_span_days'] = (
            pd.to_datetime(stats['last_time']) - pd.to_datetime(stats['first_time'])
        ).dt.days + 1
        
        # 计算交易频率（笔/天）
        stats['freq_per_day'] = stats['trans_count'] / stats['time_span_days']
        
        return stats.sort_values('total_amount', ascending=False).head(top_n)
    
    def detect_round_amount(self, thresholds=None):
        """
        检测整数金额（涉诈特征）
        
        Args:
            thresholds: 整数检测阈值列表，默认 [100, 500, 1000, 5000, 10000]
        """
        if thresholds is None:
            thresholds = [100, 500, 1000, 5000, 10000]
        
        results = {}
        
        for threshold in thresholds:
            mask = self.df['amount'] % threshold == 0
            count = mask.sum()
            ratio = mask.mean() * 100
            fraud_in_round = self.df[mask]['is_fraud'].sum() if count > 0 else 0
            fraud_ratio = self.df[mask]['is_fraud'].mean() * 100 if count > 0 else 0
            
            results[f'round_{threshold}'] = {
                'count': int(count),
                'ratio': float(ratio),
                'fraud_count': int(fraud_in_round),
                'fraud_ratio': float(fraud_ratio)
            }
        
        # 大额整数（涉诈高风险特征）
        large_round_mask = (self.df['amount'] >= 10000) & (self.df['amount'] % 1000 == 0)
        results['large_round_1000'] = {
            'count': int(large_round_mask.sum()),
            'amount': float(self.df[large_round_mask]['amount'].sum()),
            'fraud_ratio': float(self.df[large_round_mask]['is_fraud'].mean() * 100)
        }
        
        return results
    
    def transaction_frequency_analysis(self, window_minutes=5):
        """
        交易频率分析（检测快速多笔）
        
        Args:
            window_minutes: 时间窗口（分钟）
        """
        df_sorted = self.df.sort_values('transaction_time').copy()
        df_sorted['time_diff_min'] = df_sorted['transaction_time'].diff().dt.total_seconds() / 60
        
        # 找出快速连续交易
        rapid_mask = df_sorted['time_diff_min'] <= window_minutes
        rapid_count = rapid_mask.sum()
        
        # 按对手方统计快速交易
        df_sorted['is_rapid'] = rapid_mask
        rapid_by_counterparty = df_sorted[rapid_mask].groupby('counterparty').size().sort_values(ascending=False)
        
        return {
            'rapid_count': int(rapid_count),
            'rapid_ratio': float(rapid_mask.mean() * 100),
            'top_rapid_counterparties': rapid_by_counterparty.head(10).to_dict()
        }
    
    # ==================== 涉诈分析 ====================
    
    def fraud_patterns(self):
        """涉诈模式分析"""
        if len(self.fraud_df) == 0:
            return None
        
        fraud_df = self.fraud_df.copy()
        
        # 时间间隔分析
        fraud_sorted = fraud_df.sort_values('transaction_time')
        fraud_sorted['time_diff_min'] = fraud_sorted['transaction_time'].diff().dt.total_seconds() / 60
        
        rapid_count = (fraud_sorted['time_diff_min'] <= 5).sum()
        
        patterns = {
            'total_count': len(fraud_df),
            'total_amount': float(fraud_df['amount'].sum()),
            'avg_amount': float(fraud_df['amount'].mean()),
            'max_amount': float(fraud_df['amount'].max()),
            'min_amount': float(fraud_df['amount'].min()),
            'median_amount': float(fraud_df['amount'].median()),
            'hour_distribution': fraud_df['hour'].value_counts().sort_index().to_dict(),
            'weekday_distribution': fraud_df['weekday'].value_counts().sort_index().to_dict(),
            'top_counterparties': fraud_df['counterparty'].value_counts().head(10).to_dict(),
            'sources': fraud_df['source'].value_counts().to_dict(),
            'rapid_transactions': int(rapid_count),
            'time_range': {
                'first': fraud_df['transaction_time'].min(),
                'last': fraud_df['transaction_time'].max()
            }
        }
        
        return patterns
    
    def auto_detect_suspicious(self):
        """
        自动检测可疑交易（无标记时）
        基于规则引擎识别潜在涉诈行为
        """
        suspicious = []
        
        # 规则1：大额整数金额
        large_round = self.df[
            (self.df['amount'] >= 10000) & 
            (self.df['amount'] % 1000 == 0)
        ]
        if len(large_round) > 0:
            suspicious.append({
                'rule_id': 'R001',
                'rule_name': '大额整数金额',
                'risk_level': '高',
                'count': len(large_round),
                'total_amount': float(large_round['amount'].sum()),
                'description': '金额≥10000且为1000的整数倍',
                'examples': large_round[['transaction_time', 'amount', 'counterparty', 'direction']].head(3).to_dict('records')
            })
        
        # 规则2：高频小额测试交易
        small_trans = self.df[self.df['amount'] < 100]
        freq_counterparties = small_trans['counterparty'].value_counts()
        high_freq = freq_counterparties[freq_counterparties >= 5]
        if len(high_freq) > 0:
            suspicious.append({
                'rule_id': 'R002',
                'rule_name': '高频小额测试交易',
                'risk_level': '中',
                'count': len(high_freq),
                'description': '同一对手方小额(<100)交易≥5次',
                'examples': high_freq.head(5).to_dict()
            })
        
        # 规则3：夜间交易集中
        night = self.detect_night_transactions()
        if night['percentage_of_total'] > 30:
            suspicious.append({
                'rule_id': 'R003',
                'rule_name': '夜间交易集中',
                'risk_level': '中',
                'count': night['count'],
                'percentage': round(night['percentage_of_total'], 2),
                'description': '夜间(22:00-06:00)交易占比>30%'
            })
        
        # 规则4：快速多笔交易
        rapid = self.transaction_frequency_analysis(window_minutes=5)
        if rapid['rapid_count'] > 10:
            suspicious.append({
                'rule_id': 'R004',
                'rule_name': '快速多笔交易',
                'risk_level': '高',
                'count': rapid['rapid_count'],
                'description': '5分钟内连续交易>10笔',
                'examples': rapid['top_rapid_counterparties']
            })
        
        # 规则5：单一对手方大额集中
        large_expense = self.expense_df[self.expense_df['amount'] >= 50000]
        cp_large = large_expense.groupby('counterparty')['amount'].agg(['count', 'sum'])
        cp_large = cp_large[cp_large['count'] >= 3]
        if len(cp_large) > 0:
            suspicious.append({
                'rule_id': 'R005',
                'rule_name': '单一对手方大额集中',
                'risk_level': '高',
                'count': len(cp_large),
                'description': '同一对手方大额(≥50000)支出≥3次',
                'examples': cp_large.head(3).to_dict()
            })
        
        # 规则6：账户余额异常变动（需要 balance 列）
        if 'balance' in self.df.columns and self.df['balance'].notna().any():
            # 检测余额骤减
            df_with_balance = self.df[self.df['balance'].notna()].copy()
            df_with_balance['balance_diff'] = df_with_balance['balance'].diff()
            sudden_drop = df_with_balance[
                (df_with_balance['balance_diff'] < -50000) & 
                (df_with_balance['direction'] == 'expense')
            ]
            if len(sudden_drop) > 0:
                suspicious.append({
                    'rule_id': 'R006',
                    'rule_name': '余额骤减',
                    'risk_level': '高',
                    'count': len(sudden_drop),
                    'description': '单笔支出后余额减少>50000',
                    'examples': sudden_drop[['transaction_time', 'amount', 'balance', 'balance_diff']].head(3).to_dict('records')
                })
        
        # 汇总风险评分
        risk_score = sum([
            3 if s['risk_level'] == '高' else 1 
            for s in suspicious
        ])
        
        return {
            'suspicious_items': suspicious,
            'risk_score': risk_score,
            'risk_level': '高' if risk_score >= 5 else '中' if risk_score >= 2 else '低'
        }
    
    def generate_report(self):
        """生成完整分析报告"""
        report = {
            'generated_at': datetime.now(),
            'basic_stats': self.basic_stats(),
            'time_analysis': {
                'daily_trend': self.daily_trend(),
                'hourly_distribution': self.hourly_distribution(),
                'weekday_distribution': self.weekday_distribution(),
                'monthly_trend': self.monthly_trend(),
                'night_transactions': self.detect_night_transactions()
            },
            'counterparty_analysis': {
                'expense': self.counterparty_analysis(direction='expense'),
                'income': self.counterparty_analysis(direction='income')
            },
            'amount_analysis': {
                'round_amount': self.detect_round_amount(),
                'frequency': self.transaction_frequency_analysis()
            },
            'fraud_analysis': {
                'patterns': self.fraud_patterns(),
                'suspicious': self.auto_detect_suspicious()
            }
        }
        
        return report
