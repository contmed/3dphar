def get_group_selection(df):
    if df is None or df.empty:
        print("Нет данных для выбора группы.")
        return None

    group_name_col = 'GroupName'
    unique_groups = df[group_name_col].drop_duplicates().sort_values().reset_index(drop=True)
    if unique_groups.empty:
        print("В файле не найдено уникальных групп.")
        return None

    print("\nДоступные группы заболеваний:")
    for idx, group_name in enumerate(unique_groups, 1):
        print(f"{idx}. {group_name}")

    while True:
        try:
            choice = input("Выберите номер группы: ").strip()
            if not choice:
                print("Ввод не может быть пустым. Пожалуйста, попробуйте снова.")
                continue
            group_idx = int(choice) - 1
            if 0 <= group_idx < len(unique_groups):
                group_name = unique_groups.iloc[group_idx]
                return group_name
            else:
                print("Неверный номер группы. Пожалуйста, попробуйте снова.")
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите число.")
        except Exception as e:
            print(f"Произошла ошибка при выборе группы: {e}")
            return None
