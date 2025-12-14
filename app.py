from flask import Flask, render_template, jsonify, request
from data_loader import load_data, load_category_names
from matrix_generator import generate_display_matrix, style_matrix_html
import pandas as pd

app = Flask(__name__)
df = load_data()
category_names = load_category_names()


def get_atx_categories():
    if df is None:
        return []
    letters = sorted({str(code).strip()[0] for code in df['ATX_Code'].dropna() if str(code).strip() and not str(code).isspace()})
    fallback_names = {
        'A': 'Пищеварительный тракт и обмен веществ',
        'B': 'Кровь и кроветворные органы',
        'C': 'Сердечно-сосудистая система',
        'D': 'Дерматологические препараты',
        'G': 'Мочеполовая система и половые гормоны',
        'H': 'Гормональные препараты системного действия (исключая половые гормоны и инсулины)',
        'J': 'Противомикробные препараты системного действия',
        'L': 'Противоопухолевые препараты и иммуномодуляторы',
        'M': 'Опорно-двигательный аппарат',
        'N': 'Нервная система',
        'P': 'Противопаразитарные препараты, инсектициды и репелленты',
        'R': 'Дыхательная система',
        'S': 'Органы чувств',
        'V': 'Разные препараты',
    }
    return [{
        'code': letter,
        'name': category_names.get(letter, fallback_names.get(letter, ''))
    } for letter in letters]


def get_atx_children(parent_code):
    if df is None:
        return []

    parent_len = len(parent_code)
    target_len = 0

    if parent_len == 1:
        target_len = 3
    elif parent_len == 3:
        target_len = 4
    elif parent_len == 4:
        target_len = 5
    else:
        return []

    matching_codes = df['ATX_Code'].dropna().astype(str)
    mask = matching_codes.str.startswith(parent_code) & (matching_codes.str.len() >= target_len)
    filtered_codes = matching_codes[mask]

    unique_children_prefixes = set()
    for code in filtered_codes:
        unique_children_prefixes.add(code[:target_len])

    results = []
    for child_code in sorted(list(unique_children_prefixes)):
        name = category_names.get(child_code, '')
        if not name:
            group_names_for_child = df[df['ATX_Code'].astype(str).str.startswith(child_code)]['GroupName'].dropna().unique()
            name = child_code
            if len(group_names_for_child) > 0:
                found_name = False
                for gn in group_names_for_child:
                    if gn.strip() and gn.strip() != child_code:
                        name = gn
                        found_name = True
                        break
                if not found_name:
                    if group_names_for_child[0].strip():
                        name = group_names_for_child[0]

        results.append({'code': child_code, 'name': name})
    return results


def get_drug_details(atx_code):
    if df is None:
        return []
    mask = df['ATX_Code'].astype(str) == atx_code
    short_series = df.loc[mask, 'Application'].fillna('').astype(str).str.strip()
    combined = set(s for s in short_series.unique() if s and not s.isspace())
    if 'ApplicationExtended' in df.columns:
        ext_series = df.loc[mask, 'ApplicationExtended'].fillna('').astype(str).str.strip()
        combined.update(s for s in ext_series.unique() if s and not s.isspace())
    return sorted(combined, key=lambda s: s.lower())


def get_application_details(application):
    if df is None:
        return []
    target = application.strip().lower()
    app_short = df['Application'].fillna('').astype(str).str.strip().str.lower()
    mask_short = app_short == target
    mask = mask_short
    if 'ApplicationExtended' in df.columns:
        app_ext = df['ApplicationExtended'].fillna('').astype(str).str.strip().str.lower()
        mask_ext = app_ext == target
        mask = mask_short | mask_ext
    drugs_df = df.loc[mask, ['ATX_Code', 'DrugName']].drop_duplicates()
    drugs = [
        {'code': row['ATX_Code'], 'name': row['DrugName']} for _, row in drugs_df.iterrows()
    ]
    drugs = sorted(drugs, key=lambda d: d['code'])
    return drugs


def get_application_matrix(application):
    global df
    tmp = df if df is not None else load_data()
    if tmp is None or tmp.empty:
        return []
    target = str(application).strip().lower()
    app_short = tmp['Application'].fillna('').astype(str).str.strip().str.lower()
    mask = app_short == target
    if 'ApplicationExtended' in tmp.columns:
        app_ext = tmp['ApplicationExtended'].fillna('').astype(str).str.strip().str.lower()
        mask = mask | (app_ext == target)
    subset = tmp.loc[mask, ['ATX_Code', 'DrugName']].copy()
    if subset.empty:
        return []
    subset['ATX_Code'] = subset['ATX_Code'].fillna('').astype(str).str.strip()
    subset['DrugName'] = subset['DrugName'].fillna('').astype(str).str.strip()
    counts = subset.groupby(['ATX_Code', 'DrugName']).size().reset_index(name='count')
    counts = counts[(counts['ATX_Code'] != '') & (counts['DrugName'] != '')]
    counts = counts.sort_values(by=['DrugName', 'ATX_Code'])
    return [
        {'code': str(row['ATX_Code']), 'drug_name': str(row['DrugName']), 'count': int(row['count'])}
        for _, row in counts.iterrows()
    ]


@app.route('/api/application-matrix/<path:application>')
def api_application_matrix(application):
    rows = get_application_matrix(application)
    return jsonify({'application': application, 'rows': rows})


@app.route('/')
def index():
	from flask import redirect, url_for
	return redirect(url_for('atx_matrix'))


@app.route('/atx-matrix')
def atx_matrix():
    letters = get_atx_categories()
    return render_template('atx_matrix.html', letters=letters)


@app.route('/drug-details')
def drug_details_page():
    return render_template('drug_details.html')


@app.route('/subcategories/<category>')
def subcategories(category):
    subcats = get_atx_children(category)
    return jsonify(subcats)


@app.route('/atx_children/<parent_code>')
def atx_children(parent_code):
    children = get_atx_children(parent_code)
    return jsonify(children)


@app.route('/api/matrix/<atx_code_for_matrix>')
def api_matrix(atx_code_for_matrix):
    global df
    if df is None:
        df = load_data()
        if df is None:
            return jsonify({'error': 'No data loaded'}), 500

    subset_df = df[df['ATX_Code'].astype(str).str.startswith(atx_code_for_matrix)]
    if subset_df.empty:
        return jsonify({'error': 'No data to display'}), 404

    potential_group_names = subset_df['GroupName'].dropna().unique()
    actual_group_name = atx_code_for_matrix
    for gn in potential_group_names:
        if gn.strip() and gn.strip() != atx_code_for_matrix:
            actual_group_name = gn
            break
    if actual_group_name == atx_code_for_matrix and len(potential_group_names) > 0 and potential_group_names[0].strip():
        actual_group_name = potential_group_names[0]

    display_df, app_cols_to_highlight = generate_display_matrix(subset_df.copy(), actual_group_name, [])

    if display_df.empty and not app_cols_to_highlight:
        return jsonify({'error': 'No data to display'}), 404

    html_table = style_matrix_html(display_df, app_cols_to_highlight, actual_group_name)
    summary_col_name = f"Всего ({actual_group_name})" if len(app_cols_to_highlight) > 0 else None
    return jsonify({
        'matrix_html': html_table,
        'selected_code': atx_code_for_matrix,
        'group_name_used_for_matrix': actual_group_name,
        'application_columns': app_cols_to_highlight,
        'summary_column': summary_col_name
    })


@app.route('/api/rows/<prefix>')
def api_rows(prefix):
    global df
    if df is None:
        tmp = load_data()
    else:
        tmp = df
    if tmp is None:
        return jsonify({'rows': []})
    subset = tmp[tmp['ATX_Code'].astype(str).str.startswith(prefix)].copy()
    if subset.empty:
        return jsonify({'rows': []})
    cols = ['ATX_Code', 'DrugName', 'Application', 'GroupName']
    rows = []
    for _, row in subset.iterrows():
        rows.append({
            'ATX_Code': str(row.get('ATX_Code', '')).strip(),
            'DrugName': str(row.get('DrugName', '')).strip(),
            'Application': str(row.get('Application', '')).strip(),
            'GroupName': str(row.get('GroupName', '')).strip(),
        })
    return jsonify({'rows': rows})


@app.route('/drug/<atx_code>')
def drug_details(atx_code):
    applications = get_drug_details(atx_code)
    return jsonify({'atx_code': atx_code, 'applications': applications})


@app.route('/application/<application>')
def application_details(application):
    drugs = get_application_details(application)
    return jsonify({'application': application, 'drugs': drugs})


@app.route('/search')
def search():
	global df
	query = request.args.get('q', '')
	if not query or len(query.strip()) == 0:
		return jsonify({'drugs': [], 'applications': []})
	if df is None:
		df = load_data()
		if df is None:
			return jsonify({'drugs': [], 'applications': []})
	q = query.strip()
	atx_series = df['ATX_Code'].fillna('').astype(str)
	name_series = df['DrugName'].fillna('').astype(str) if 'DrugName' in df.columns else None
	if name_series is not None:
		drug_mask = atx_series.str.contains(q, case=False, na=False) | name_series.str.contains(q, case=False, na=False)
	else:
		drug_mask = atx_series.str.contains(q, case=False, na=False)
	filtered = df[drug_mask].copy()
	filtered['ATX_Code'] = filtered['ATX_Code'].fillna('').astype(str).str.strip()
	filtered['DrugName'] = filtered['DrugName'].fillna('').astype(str).str.strip() if 'DrugName' in filtered.columns else ''
	drugs = []
	for code in sorted(filtered['ATX_Code'].dropna().unique()):
		if not code:
			continue
		names = []
		if 'DrugName' in filtered.columns:
			names = [n for n in sorted(filtered.loc[filtered['ATX_Code'] == code, 'DrugName'].dropna().unique()) if n]
		rep_name = names[0] if names else ''
		drugs.append({'code': code, 'name': rep_name})
	app_short = df['Application'].fillna('').astype(str)
	mask_short = app_short.str.contains(q, case=False, na=False)
	if 'ApplicationExtended' in df.columns:
		app_ext = df['ApplicationExtended'].fillna('').astype(str)
		mask_ext = app_ext.str.contains(q, case=False, na=False)
		apps = pd.Series(pd.concat([app_short[mask_short], app_ext[mask_ext]])).dropna().astype(str).unique()
	else:
		apps = app_short[mask_short].dropna().astype(str).unique()
	applications = sorted(apps)
	return jsonify({'drugs': drugs, 'applications': applications})


if __name__ == '__main__':
	import os
	port = int(os.environ.get('PORT', '8000'))
	app.run(host='0.0.0.0', port=port, debug=False) 