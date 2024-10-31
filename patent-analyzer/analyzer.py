import pandas as pd
import random
import matplotlib.pyplot as plt
import argparse
import os.path
import json

GRANT_COUNTRY = 'Страна выдачи'
APPLY_COUNTRY = 'Страна заявитель'
APPLIERS = 'Заявитель'
APPLY_YEAR = 'Год подачи заявки'
CLASSIFICATOR = 'Классификатор(ы)'

KEY = 'Ключ'
ORGANIZATIONS = 'Организации'
COUNTRIES = 'Страны'
PUBLICATION_YEAR = 'Год публикации'

FIGURE_SIZE = (14, 7)

'''Подготовка датафреймов для построения диаграмм или записи в файл'''


def split_dataframes(dataframe, units_limit, percent_limit, *column_names):
    result_dataframes = {}

    for column_name in column_names:
        series_column = dataframe[column_name]
        column_divided = series_column.str.split('; ', expand=True)
        column_list = list()

        for index in range(column_divided.shape[1]):
            col = column_divided.iloc[:, index]
            for i in col:
                column_list.append(i)

        column_list_filtered = list(filter(None, column_list))
        df_divided = pd.DataFrame(column_list_filtered,
                                  columns=[column_name])
        df_top = df_divided[column_name].value_counts()
        index_series = pd.Series(df_top.index)
        df_result = pd.DataFrame({column_name: index_series,
                                  'Количество': df_top.values},
                                 index=index_series.index)
        if len(df_top.axes[0]) <= units_limit:
            result_dataframes[column_name] = df_result
        else:
            country_index = 0
            other = 0
            num = 0
            for i in df_result.Количество[::-1]:
                num += i
                if num <= percent_limit * df_result.Количество.sum():
                    other = num
                    country_index += 1
            df_result = pd.DataFrame({column_name: df_result[column_name].head(len(df_result) -
                                                                               country_index),
                                      'Количество':
                                          df_result.Количество.head(len(df_result) -
                                                                    country_index)})

            df_result.loc[-1] = ['Other', other]
            result_dataframes[column_name] = df_result

    return result_dataframes


'''Построение круговой диаграммы'''


def diagram(dataframe, column_name, diagram_title, file_name, some_prefix):
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    colors_list = list()
    random.seed(1234)
    for _ in range(len(dataframe) - 1):
        r = random.random()
        b = random.random()
        g = random.random()
        color = (r, g, b)
        colors_list.append(color)
    colors = colors_list + [(0.5, 0.5, 0.5)]

    ax.pie(dataframe.Количество, labels=dataframe[column_name],
           colors=colors, autopct='%1.1f%%')
    ax.set(title=diagram_title)
    name = some_prefix + file_name
    fig.savefig(name)


'''Построение столбчатой диаграммы для иллюстрации распределения по годам'''


def bar(dataframe, column_name, file_name, diagram_title, some_prefix):
    df_bar = dataframe[column_name].value_counts()
    fig, ax = plt.subplots(figsize=(10, 7))
    _ = plt.bar(df_bar.index, df_bar.values)
    ax.set_xticks(df_bar.index)
    ax.set(title=diagram_title)
    name = some_prefix + file_name
    fig.savefig(name)


'''Запись датафрейма в файл'''


def file_out(file_name, dataframe, some_prefix):
    dataframe[' '] = ' '
    dataframe.set_index(' ', inplace=True)
    name = some_prefix + file_name
    with open(name, 'w', encoding='utf-8') as outfile:
        dataframe.to_string(outfile)


'''Чтение файла конфигурации'''


def load_json(file_name):
    with open(file_name, encoding='utf-8') as config_file:
        data = json.load(config_file)
    return data


'''Обработка данных конфигурационного файла'''


def process_config(data, settings_name, dataframe, text_file_name, some_prefix):
    column_name = data[settings_name]['column_name']
    diagram_title = data[settings_name]['diagram_title']
    file_name = data[settings_name]['file_name']
    units_limit = data[settings_name]['units_limit']
    percent_limit = data[settings_name]['percent_limit']
    result = split_dataframes(dataframe, units_limit, percent_limit, column_name)[column_name]
    diagram(result, column_name,
            diagram_title, file_name, some_prefix)
    file_out(text_file_name, result, some_prefix)


'''Анализатор патентов'''


def process_patents(dataframe_all, some_prefix, settings):
    df = dataframe_all[[GRANT_COUNTRY, APPLY_COUNTRY, APPLIERS,
                        APPLY_YEAR, CLASSIFICATOR]]

    process_config(settings, 'grant_countries_settings', df, 'patents_granting_countries.txt', some_prefix)
    process_config(settings, 'apply_countries_settings', df, 'patents_applying_countries.txt', some_prefix)
    process_config(settings, 'appliers_settings', df, 'patents_appliers.txt', some_prefix)

    column_name_c = settings['classificator_settings']['column_name']
    units_limit_c = settings['classificator_settings']['units_limit']
    percent_limit_c = settings['classificator_settings']['percent_limit']

    classificator = split_dataframes(df, units_limit_c, percent_limit_c, column_name_c)[column_name_c]

    file_out('patents_classificator.txt', classificator, some_prefix)

    bar(df, 'Год подачи заявки', 'patents_years_bar', 'Распределение патентов по годам подачи заявки', some_prefix)

    print('Анализ патентов завершен')


'''Анализатор научных статей'''


def process_papers(dataframe_all, some_prefix, settings):
    df = dataframe_all[[KEY, ORGANIZATIONS, COUNTRIES, PUBLICATION_YEAR]]

    column_name_o = settings['organizations_settings']['column_name']
    units_limit_o = settings['organizations_settings']['units_limit']
    percent_limit_o = settings['organizations_settings']['percent_limit']

    df_orgs = split_dataframes(df, units_limit_o, percent_limit_o, column_name_o)[column_name_o]

    process_config(settings, 'countries_settings', df, 'papers_countries_file.txt', some_prefix)

    file_out('papers_orgs_file.txt', df_orgs, some_prefix)

    bar(df, 'Год публикации', 'papers_years_bar', 'Распределение научных статей по годам публикации',
        some_prefix)

    print('Анализ научных статей завершен')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='patents',
                        choices=['patents', 'papers'],
                        help='program mode')
    parser.add_argument('path_to_file', type=str,
                        help='path to XLSX input file')
    parser.add_argument('--prefix', type=str, default='',
                        help='prefix for generated files')
    parser.add_argument('--config', type=str, default='config.json',
                        help='path to JSON config')
    inputs = parser.parse_args()

    if not os.path.isfile(inputs.path_to_file):
        print('Невозможно открыть файл')
    elif not (inputs.path_to_file.endswith('.xlsx') | inputs.path_to_file.endswith('.ods')
              | inputs.path_to_file.endswith('.xls')):
        print('Некорректный формат файла')
    else:
        df_all = pd.read_excel(inputs.path_to_file)

        prefix = inputs.prefix
        config_file = inputs.config
        settings = load_json(config_file)

        if inputs.mode == 'patents':
            process_patents(df_all, prefix, settings)
        if inputs.mode == 'papers':
            process_papers(df_all, prefix, settings)


if __name__ == '__main__':
    main()
