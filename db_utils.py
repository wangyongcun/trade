import os
import sqlite3
import pandas as pd
from typing import Optional, Dict, Any, Tuple, List

DB_PATH = os.path.join('stock-data', 'stock_data.db')

# 可能的列名映射候选
CODE_CANDIDATES = ['code', 'ts_code', 'symbol', 'stock_code']
DATE_CANDIDATES = ['trade_date', 'date', 'trade_dt', 'time', 'dt']
OPEN_CANDIDATES = ['open']
HIGH_CANDIDATES = ['high']
LOW_CANDIDATES = ['low']
CLOSE_CANDIDATES = ['close', 'adj_close', 'close_price']
VOL_CANDIDATES = ['vol', 'volume', 'volumn']
NAME_CANDIDATES = ['name', 'stock_name', 'sname', 'display_name']

PREFERRED_TABLE_KEYWORDS = ['price', 'kline', 'daily', 'quote', 'quotes', 'stock']


def _get_conn() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f'数据库文件未找到: {DB_PATH}')
    conn = sqlite3.connect(DB_PATH)
    return conn


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [r[0] for r in cur.fetchall()]


def _list_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    rows = cur.fetchall()
    # row: (cid, name, type, notnull, dflt_value, pk)
    return [r[1] for r in rows]


def _find_first_match(cands: List[str], cols_lower: Dict[str, str]) -> Optional[str]:
    for cand in cands:
        if cand in cols_lower:
            return cols_lower[cand]
    return None


def _score_table(table: str) -> int:
    # 表名中包含优先关键字的得分更高
    name_lower = table.lower()
    for kw in PREFERRED_TABLE_KEYWORDS:
        if kw in name_lower:
            return 10
    return 0


def _find_table_and_columns(conn: sqlite3.Connection) -> Tuple[str, Dict[str, Optional[str]]]:
    """
    在数据库中自动寻找包含价格信息的表，并识别关键列名。
    返回：(表名, 列名映射字典)
    列名映射字典的键包括：code, date, open, high, low, close, vol(可选), name(可选)
    """
    tables = _list_tables(conn)
    candidates: List[Tuple[int, str, Dict[str, Optional[str]]]] = []

    for t in tables:
        cols = _list_columns(conn, t)
        if not cols:
            continue
        # 建立小写 -> 原始列名 的映射
        cols_lower_map = {c.lower(): c for c in cols}

        code_col = _find_first_match(CODE_CANDIDATES, cols_lower_map)
        date_col = _find_first_match(DATE_CANDIDATES, cols_lower_map)
        open_col = _find_first_match(OPEN_CANDIDATES, cols_lower_map)
        high_col = _find_first_match(HIGH_CANDIDATES, cols_lower_map)
        low_col = _find_first_match(LOW_CANDIDATES, cols_lower_map)
        close_col = _find_first_match(CLOSE_CANDIDATES, cols_lower_map)
        vol_col = _find_first_match(VOL_CANDIDATES, cols_lower_map)
        name_col = _find_first_match(NAME_CANDIDATES, cols_lower_map)

        required_ok = all([code_col, date_col, open_col, high_col, low_col, close_col])
        if required_ok:
            score = 100 + _score_table(t)
            # 小加成：存在成交量/名称列的表更优
            if vol_col:
                score += 2
            if name_col:
                score += 1
            candidates.append((
                score,
                t,
                {
                    'code': code_col,
                    'date': date_col,
                    'open': open_col,
                    'high': high_col,
                    'low': low_col,
                    'close': close_col,
                    'vol': vol_col,
                    'name': name_col
                }
            ))

    if not candidates:
        raise RuntimeError('在数据库中未能识别包含股票价格数据的表，请检查表结构。')
    # 选择得分最高的表
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, table_name, colmap = candidates[0]
    return table_name, colmap


def _format_trade_date(df: pd.DataFrame, date_col: str) -> pd.Series:
    # 尝试把所有分隔符去掉，以识别 yyyymmdd
    s_raw = df[date_col]
    s_str = s_raw.astype(str).str.replace('-', '', regex=False).str.replace('/', '', regex=False)
    # 优先按 yyyymmdd 解析
    s_dt = pd.to_datetime(s_str, format='%Y%m%d', errors='coerce')
    # 对没解析到的，再用自动解析
    mask = s_dt.isna()
    if mask.any():
        s_dt2 = pd.to_datetime(s_raw, errors='coerce', infer_datetime_format=True)
        s_dt = s_dt.where(~mask, s_dt2)
    # 最终格式化为 YYYY/MM/DD
    return s_dt.dt.strftime('%Y/%m/%d')


def read_stock_data(code: str) -> pd.DataFrame:
    """
    读取单只股票的历史K线数据，返回包含列：
    trade_date(YYYY/MM/DD), open, high, low, close, 以及可选的 vol
    """
    conn = _get_conn()
    try:
        table, colmap = _find_table_and_columns(conn)
        code_col = colmap['code']
        date_col = colmap['date']
        cols = [colmap['open'], colmap['high'], colmap['low'], colmap['close'], date_col]
        if colmap['vol']:
            cols.append(colmap['vol'])

        sel_cols = ', '.join([f'"{c}"' for c in cols])
        sql = f'SELECT {sel_cols} FROM "{table}" WHERE "{code_col}" = ?'
        df = pd.read_sql_query(sql, conn, params=[code])

        # 统一列名
        df = df.rename(columns={
            colmap['open']: 'open',
            colmap['high']: 'high',
            colmap['low']: 'low',
            colmap['close']: 'close',
        })
        if colmap['vol'] and colmap['vol'] in df.columns:
            df = df.rename(columns={colmap['vol']: 'vol'})

        # 统一 trade_date
        df['trade_date'] = _format_trade_date(df, date_col)

        # 排序
        df = df.sort_values('trade_date').reset_index(drop=True)
        return df[['trade_date', 'open', 'high', 'low', 'close'] + (['vol'] if 'vol' in df.columns else [])]
    finally:
        conn.close()


def get_stock_list() -> List[Dict[str, str]]:
    """
    读取股票列表，返回 [{'code': '000001.SZ', 'name': '平安银行'}, ...]
    如果不存在名称列，则使用 code 作为 name。
    """
    conn = _get_conn()
    try:
        table, colmap = _find_table_and_columns(conn)
        code_col = colmap['code']
        name_col = colmap['name']

        if name_col:
            sql = f'SELECT DISTINCT "{code_col}" AS code, "{name_col}" AS name FROM "{table}" ORDER BY code'
            df = pd.read_sql_query(sql, conn)
            df['name'] = df['name'].fillna(df['code'])
        else:
            sql = f'SELECT DISTINCT "{code_col}" AS code FROM "{table}" ORDER BY code'
            df = pd.read_sql_query(sql, conn)
            df['name'] = df['code']

        return [{'code': r['code'], 'name': r['name']} for _, r in df.iterrows()]
    finally:
        conn.close()


def get_stock_name(code: str) -> str:
    """
    获取单个股票名称；若不存在名称列或查不到，返回 code
    """
    conn = _get_conn()
    try:
        table, colmap = _find_table_and_columns(conn)
        code_col = colmap['code']
        name_col = colmap['name']
        if not name_col:
            return code
        sql = f'SELECT "{name_col}" AS name FROM "{table}" WHERE "{code_col}" = ? LIMIT 1'
        df = pd.read_sql_query(sql, conn, params=[code])
        if df.empty or pd.isna(df.loc[0, 'name']):
            return code
        return str(df.loc[0, 'name'])
    finally:
        conn.close()