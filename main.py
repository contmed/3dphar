from data_loader import create_sample_excel, load_data
from group_selection import get_group_selection
from matrix_generator import generate_display_matrix, style_matrix_html

def main():
    df = load_data()
    if df is None:
        print("Не удалось загрузить данные. Программа завершается.")
        return
    history_selected_groups = []
    while True:
        current_group_name = get_group_selection(df)
        if current_group_name is None:
            break
        print(f"\n--- Генерируется матрица для группы: {current_group_name} ---")
        display_df, app_cols_to_highlight = generate_display_matrix(df.copy(), current_group_name, list(history_selected_groups))
        if display_df.empty and not app_cols_to_highlight:
            print(f"Для группы '{current_group_name}' не найдено препаратов или определенных областей применения для отображения.")
        else:
            html_table = style_matrix_html(display_df, app_cols_to_highlight, current_group_name)
            print("\nHTML для отображения матрицы:")
            print(html_table)
            try:
                safe_group_name = "".join(c if c.isalnum() else "_" for c in current_group_name)
                filename = f"matrix_output_{safe_group_name}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("<!DOCTYPE html>\n<html lang='ru'>\n<head>\n<meta charset='UTF-8'>\n")
                    f.write("<title>Матрица препаратов</title>\n")
                    f.write("<style>\n")
                    f.write("body { font-family: sans-serif; margin: 20px; }\n")
                    f.write("table { border-collapse: collapse; margin-top: 20px; width: auto; }\n")
                    f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n")
                    f.write("th { background-color: #f2f2f2; }\n")
                    f.write("caption { font-size: 1.2em; margin-bottom: 10px; font-weight: bold; }\n")
                    f.write("</style>\n</head>\n<body>\n")
                    f.write(html_table)
                    f.write("\n</body>\n</html>")
                print(f"HTML сохранен в файл: {filename}")
            except Exception as e:
                print(f"Ошибка при сохранении HTML в файл: {e}")
        if current_group_name not in history_selected_groups:
            history_selected_groups.append(current_group_name)
        cont = input("\nХотите выбрать другую группу? (да/нет): ").strip().lower()
        if cont != 'да':
            break
    print("\nПрограмма завершена.")

if __name__ == "__main__":
    main()
