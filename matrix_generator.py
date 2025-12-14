import pandas as pd
import re


def generate_display_matrix(full_df, current_group_name, history_selected_groups_info):
    if full_df is None or full_df.empty:
        return pd.DataFrame(), []
    current_group_data_for_pivot = full_df[full_df['GroupName'] == current_group_name]
    apps = full_df[full_df['GroupName'] == current_group_name]['Application'].dropna().astype(str)
    applications_defined_for_current_group = sorted([a for a in apps.unique() if a and not a.isspace()])
    if not current_group_data_for_pivot.empty:
        matrix_part1 = current_group_data_for_pivot.pivot_table(
            index='ATX_Code',
            columns='Application',
            aggfunc='size', 
            fill_value=0
        )
        matrix_part1 = matrix_part1.map(lambda x: 1 if x > 0 else 0)
        for app_name in applications_defined_for_current_group:
            if app_name not in matrix_part1.columns:
                matrix_part1[app_name] = 0 
        if applications_defined_for_current_group:
             matrix_part1 = matrix_part1.reindex(columns=applications_defined_for_current_group, fill_value=0)
        else:
             matrix_part1 = pd.DataFrame(index=matrix_part1.index)
    elif applications_defined_for_current_group:
        matrix_part1 = pd.DataFrame(columns=applications_defined_for_current_group)
        matrix_part1.index.name = 'ATX_Code'
    else:
        matrix_part1 = pd.DataFrame()
        matrix_part1.index.name = 'ATX_Code'
    atx_codes_in_part1 = set(matrix_part1.index) if not matrix_part1.empty else set()
    all_atx_codes_for_matrix = set(atx_codes_in_part1)
    history_columns_data = {}
    for prev_group_name in history_selected_groups_info:
        prev_group_data = full_df[full_df['GroupName'] == prev_group_name]
        if not prev_group_data.empty:
            count_series = prev_group_data.groupby('ATX_Code')['Application'].count()
            count_series.name = prev_group_name
            history_columns_data[prev_group_name] = count_series
            all_atx_codes_for_matrix.update(count_series.index)
    matrix_part2_index = list(all_atx_codes_for_matrix) if all_atx_codes_for_matrix else None
    matrix_part2 = pd.DataFrame(index=matrix_part2_index)
    if not matrix_part2.empty:
        matrix_part2.index.name = 'ATX_Code'
    for col_name, series_data in history_columns_data.items():
        matrix_part2 = matrix_part2.join(series_data, how='left')
    matrix_part2 = matrix_part2.fillna(0).astype(int)
    if not matrix_part1.empty:
        matrix_part1 = matrix_part1.reindex(index=matrix_part2_index, fill_value=0)
    elif applications_defined_for_current_group and matrix_part2_index is not None:
        matrix_part1 = pd.DataFrame(0, index=matrix_part2_index, columns=applications_defined_for_current_group)
        if not matrix_part1.empty: matrix_part1.index.name = 'ATX_Code'
    if not matrix_part1.empty and not matrix_part2.empty:
        final_matrix = matrix_part1.join(matrix_part2, how='outer') 
    elif not matrix_part1.empty:
        final_matrix = matrix_part1
    elif not matrix_part2.empty:
        if applications_defined_for_current_group:
            temp_current_apps_df = pd.DataFrame(0, index=matrix_part2.index, columns=applications_defined_for_current_group)
            if not temp_current_apps_df.empty: temp_current_apps_df.index.name = 'ATX_Code'
            final_matrix = temp_current_apps_df.join(matrix_part2, how='outer')
        else:
            final_matrix = matrix_part2
    else:
        if applications_defined_for_current_group:
            final_matrix = pd.DataFrame(columns=applications_defined_for_current_group)
            final_matrix.index.name = 'ATX_Code'
        else:
            final_matrix = pd.DataFrame()
            final_matrix.index.name = 'ATX_Code'
    final_matrix = final_matrix.fillna(0)
    hist_col_names = matrix_part2.columns.tolist() if not matrix_part2.empty else []
    for app_col in applications_defined_for_current_group:
        if app_col not in final_matrix.columns:
            final_matrix[app_col] = 0
    for hist_col in hist_col_names:
        if hist_col not in final_matrix.columns:
            final_matrix[hist_col] = 0
    desired_column_order = []
    seen_in_order = set()
    for col in applications_defined_for_current_group:
        if col not in seen_in_order:
            desired_column_order.append(col)
            seen_in_order.add(col)
    for col in hist_col_names:
        if col not in seen_in_order:
            desired_column_order.append(col)
            seen_in_order.add(col)
    for col in final_matrix.columns:
        if col not in seen_in_order:
            desired_column_order.append(col)
    if not final_matrix.empty:
        final_matrix = final_matrix.reindex(columns=desired_column_order).fillna(0)
        for col in final_matrix.columns:
            if col in applications_defined_for_current_group:
                final_matrix[col] = final_matrix[col].astype(int)
            else:
                final_matrix[col] = final_matrix[col].astype(int)
    elif applications_defined_for_current_group:
         final_matrix = pd.DataFrame(columns=applications_defined_for_current_group)
         if not final_matrix.empty or applications_defined_for_current_group : final_matrix.index.name = 'ATX_Code'
    if applications_defined_for_current_group and not final_matrix.empty:
        current_app_cols_in_final = [c for c in applications_defined_for_current_group if c in final_matrix.columns]
        if current_app_cols_in_final:
            summary_col_name = f'Всего ({current_group_name})'
            final_matrix[summary_col_name] = final_matrix[current_app_cols_in_final].sum(axis=1).astype(int)
            cols_without_summary = [c for c in final_matrix.columns if c != summary_col_name]
            final_matrix = final_matrix.reindex(columns=[summary_col_name] + cols_without_summary)
    if not final_matrix.empty and 'DrugName' in full_df.columns:
        atx_to_name = full_df.drop_duplicates('ATX_Code').set_index('ATX_Code')['DrugName'].to_dict()
        def clean_name(name):
            return name.lstrip(' _\u00A0').strip()
        new_index = []
        for code in final_matrix.index:
            name = clean_name(atx_to_name.get(code, ''))
            if name:
                html = f'<span style="color:#222;font-weight:normal;">{name}</span><br><span class="atx-code clickable">{code}</span>'
            else:
                html = f'<span class="atx-code clickable">{code}</span>'
            new_index.append(html)
        final_matrix.index = new_index
        final_matrix.index.name = 'Препарат'
    return final_matrix, applications_defined_for_current_group


def style_matrix_html(df_to_style, application_columns_to_highlight, current_group_name_for_caption=""):
    if df_to_style.empty and not application_columns_to_highlight:
        return f"<p>Нет данных для отображения для группы '{current_group_name_for_caption}'.</p>"
    if df_to_style.empty and application_columns_to_highlight:
        df_to_style = pd.DataFrame(columns=application_columns_to_highlight)
        df_to_style.index.name = 'Препарат'
        df_to_style.columns.name = 'Показания'
    df_to_style = df_to_style.rename_axis('Препарат', axis='index').rename_axis('Показания', axis='columns')
    def highlighter(data_row):
        styles = [''] * len(data_row)
        for i, col_name in enumerate(data_row.index):
            if col_name in application_columns_to_highlight and col_name in data_row.index and data_row[col_name] == 1:
                styles[i] = 'background-color: lightgreen'
        return styles
    actual_app_cols_in_df = [col for col in application_columns_to_highlight if col in df_to_style.columns]
    if not df_to_style.empty and actual_app_cols_in_df:
         styled_df = df_to_style.style.apply(highlighter, axis=1, subset=pd.IndexSlice[:, actual_app_cols_in_df])
    elif not df_to_style.empty:
         styled_df = df_to_style.style
    else:
        empty_html = pd.DataFrame(columns=application_columns_to_highlight if application_columns_to_highlight else [' ']).to_html(classes='dataframe table table-striped table-bordered', escape=False)
        return f"<h3>Матрица для группы: {current_group_name_for_caption}</h3>{empty_html}<p>Нет препаратов для отображения в данной группе.</p>"
    if current_group_name_for_caption:
        styled_df = styled_df.set_caption(f"Матрица для группы: {current_group_name_for_caption}")
    html_output = styled_df.to_html(classes='dataframe table table-striped table-bordered', escape=False, index_names=True)
    html_output = re.sub(
        r'(<th[^>]*class="[^"]*index_name[^"]*"[^>]*>)[^<]*</th>',
        r'\1Показания &#8594;<br>Препарат &#8595;</th>',
        html_output,
        count=1
    )
    html_output = re.sub(
        r'(<thead>.*?</tr>)(\s*<tr>.*?Препарат.*?</tr>)',
        r'\1',
        html_output,
        flags=re.DOTALL
    )
    return html_output
