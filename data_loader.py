import pandas as pd
import re


def split_atx_and_name(value):
    if pd.isna(value):
        return '', ''
    match = re.match(r'^([A-Z0-9]+)\s*(.*)$', str(value).strip())
    if match:
        code = match.group(1)
        name = match.group(2).lstrip(' _\u00A0').strip()
        return code, name
    return value, ''


def load_data(filepath="input_A.xlsx"):
    try:
        raw = pd.read_excel(filepath)
        if raw is None or raw.empty:
            print(f"Ошибка: Файл '{filepath}' пуст или не содержит данных.")
            return None

        df = raw.copy()
        rename_map = {}
        for col in list(df.columns):
            lc = str(col).strip().lower()
            if 'атх' in lc and ('актив' in lc or 'атхактив' in lc or 'atx' in lc):
                rename_map[col] = 'ATX_Code'
            elif 'область применения' in lc and 'расшир' in lc:
                rename_map[col] = 'ApplicationExtended'
            elif ('область применения' in lc and 'крат' in lc) or lc == 'облприм':
                rename_map[col] = 'Application'
            elif ('группа показ' in lc) or lc in ('назв гр', 'назвгр', 'название гр', 'название группы'):
                rename_map[col] = 'GroupName'
        if rename_map:
            df = df.rename(columns=rename_map)

        cols = list(raw.columns)
        if 'ATX_Code' not in df.columns and len(cols) >= 1:
            df = df.rename(columns={cols[0]: 'ATX_Code'})
        if 'Application' not in df.columns and len(cols) >= 3:
            df = df.rename(columns={cols[2]: 'Application'})
        if 'ApplicationExtended' not in df.columns and len(cols) >= 4:
            df = df.rename(columns={cols[3]: 'ApplicationExtended'})
        if 'GroupName' not in df.columns and len(cols) >= 5:
            df = df.rename(columns={cols[4]: 'GroupName'})

        for required in ['ATX_Code', 'Application', 'GroupName']:
            if required not in df.columns:
                print(f"Предупреждение: отсутствует обязательная колонка '{required}' в '{filepath}'. Будет создана пустая.")
                df[required] = ''
        if 'ApplicationExtended' not in df.columns:
            df['ApplicationExtended'] = ''

        df[['ATX_Code', 'DrugName']] = df['ATX_Code'].apply(lambda x: pd.Series(split_atx_and_name(x)))
        if 'Назв' in df.columns:
            name_series = df['Назв'].fillna('').astype(str).str.strip()
            if 'DrugName' not in df.columns or df['DrugName'].fillna('').astype(str).str.strip().eq('').all():
                df['DrugName'] = name_series
            else:
                mask_empty = df['DrugName'].fillna('').astype(str).str.strip().eq('')
                df.loc[mask_empty, 'DrugName'] = name_series[mask_empty]

        df['ATX_Code'] = df['ATX_Code'].fillna('').astype(str).str.strip()
        df['DrugName'] = df['DrugName'].fillna('').astype(str).str.strip()
        df['Application'] = df['Application'].fillna('').astype(str).str.strip()
        df['ApplicationExtended'] = df['ApplicationExtended'].fillna('').astype(str).str.strip()
        df['GroupName'] = df['GroupName'].fillna('').astype(str).str.strip()

        df = df[df['ATX_Code'].astype(str).str.len() > 0]

        return df.reset_index(drop=True)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{filepath}' не найден.")
        print("Пожалуйста, убедитесь, что файл существует в той же директории, что и скрипт.")
        return None
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return None


def load_category_names(filepath="categories.xlsx"):
    try:
        df = pd.read_excel(filepath)
        if df is None or df.empty or df.shape[1] < 2:
            return {}
        code_col = df.columns[0]
        name_col = df.columns[1]
        mapping = {}
        for _, row in df.iterrows():
            code = str(row[code_col]).strip() if pd.notna(row[code_col]) else ''
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ''
            if code:
                mapping[code] = name
        return mapping
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Предупреждение: не удалось загрузить категории из '{filepath}': {e}")
        return {}
