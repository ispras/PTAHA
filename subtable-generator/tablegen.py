import pandas as pd
import numpy as np
import argparse

# store dataframe columns which are used by scripts
read = 'Читал'
year_apply = 'Год подачи заявки'
classifs = 'Классификатор(ы)'
country_gave = 'Страна выдачи'
country_apply = 'Страна заявитель'
inventor = 'Изобретатель'
invention = 'Название'
act_info = 'Сведения о действии'
fullid = 'Full ID'
classif_ind = 'Классификационный индекс (IPC)'
applr = 'Заявитель'
applctn_num = 'Номер заявки'
prior_date = 'Дата приоритета'
prior_docs = 'Приоритетные документы'
publish_date = 'Дата публикации'


def extract_data(path):
    # CSV, ODT, XLSX formats are supported
    is_excel = path.endswith('.xlsx') or path.endswith('.ods')
    data = pd.read_excel(path) if is_excel else pd.read_csv(path)
    # filter unused columns out
    filtered_data = data.drop('№', axis=1)
    return [filtered_data, str(path.split('.')[-1])]


def reformatting_of_fullid(full_id: str):
    seps = full_id.split('-')
    res = seps[0] + '-' + seps[1] + ' (' + seps[2] + ')'
    return res


def datetime_to_date(l_datetime: str):
    res = l_datetime.split(' ')[0]
    return res


def tags_of_other_countries(mdf):
    # getting indexes of columns with names of other countries, which also published patent (right part of the table)
    left_tag = mdf.columns.get_loc('Tag') + 1  # countries list starts from next after Tag column
    right_tag = mdf.shape[1]  # and ends in the end of dataframe
    return [left_tag, right_tag]


def find_index_of_first_country(df):
    alph = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
            'V', 'W', 'X', 'Y', 'Z']
    cols = df.columns
    i = 0
    while not (len(cols[i]) == 2 and cols[i][0] in alph and cols[i][1] in alph):
        i += 1
    return i


def gen_df_for_6_1_table(mdf):
    # Table 6.1 (Patent documentation) generation

    # column names for Table 6.1
    c1 = 'Страна выдачи,\nномер и вид охранного документа.\nКлассификационный индекс'
    c2 = ('Заявитель (патентообладатель); страна.\nНомер заявки, дата приоритета, конвенционный приоритет,\n'
          'дата публикации')
    c3 = 'Название изобретения\n(полной модели, образца)'
    c4 = 'Сведения о действии охранного документа\nили причина его аннулирования'

    ndata = ''
    rows_num = mdf.shape[0]  # stored number of rows in df
    result_data_storage = [[0] * 4 for _ in range(rows_num)]
    for i in range(rows_num):
        other_publishes = []
        for tag in range(tags_of_other_countries(mdf)[0], tags_of_other_countries(mdf)[1]):
            if pd.notnull(mdf.iloc[:, tag][i]):
                other_publishes.append(mdf.iloc[:, tag][i])
        for k in range(4):
            if k == 0:
                ndata = reformatting_of_fullid(str(mdf[fullid][i])) + '\nМПК: ' + ';\n'.join(
                    mdf[classif_ind][i].split(';')) + '\nТакже опубликовано, как: ' + ',\n'.join(other_publishes)
            elif k == 1:
                ndata = 'Заявитель(и ); страна: ' + str(mdf[applr][i]) + '; ' + \
                        str(mdf[country_gave][i]) + '. \nИзобретатель(и): ' + \
                        str(mdf[inventor][i]) + '\nЗаявка: ' + \
                        str(mdf[applctn_num][i]) + '\nДата приоритета: ' + \
                        str(pd.to_datetime(mdf[prior_date]).dt.strftime('%d-%m-%Y')[i]) + \
                        '\nПриоритетные документы:\n' +\
                        str(mdf[prior_docs][i]) + '\nОпубликовано: ' + \
                        str(pd.to_datetime(mdf[publish_date]).dt.strftime('%d-%m-%Y')[i])
            elif k == 2:
                ndata = str(mdf[invention][i])
            elif k == 3:
                ndata = str(mdf[act_info][i])
            result_data_storage[i][k] = ndata  # pep-8 error occurs of pycharm bug
    df_6_1 = pd.DataFrame(result_data_storage, columns=[c1, c2, c3, c4])
    return df_6_1


def gen_df_for_6_4_table(mdf):
    # Table 6.4 (The number of published security documents by year) generation

    c1 = 'Количество патентов, опубликованных заявок по годам подачи заявки (исключая патенты-аналоги)'
    c2 = 'Объект техники и его составные части'
    c3 = 'Страна'

    left_tag = tags_of_other_countries(mdf)[0]  # countries list starts from next after Tag column
    right_tag = tags_of_other_countries(mdf)[1]  # and ends in the end of dataframe
    other_countries = mdf.iloc[:, left_tag:right_tag]

    data64 = pd.concat([mdf[country_apply], mdf[classifs], mdf[year_apply], other_countries], axis=1)
    years = sorted(mdf[year_apply].unique().astype(int))
    """one cell can consist of several classifiers. Hereafter we divide them with '.' and add
     to the list of all unique classifiers."""
    classifiers = mdf[classifs].unique()
    unique_clsf_splited = []
    for i in range(len(classifiers)):
        split = classifiers[i].split('.')
        for j in range(len(split)):
            unique_clsf_splited.append(split[j])
    unique_clsf_splited = list(set(unique_clsf_splited))

    all_countries_for_classifs = []
    countries_for_classif = []
    years_counts = {}

    for classifier in unique_clsf_splited:
        for index, row in data64.iterrows():
            if classifier in row[classifs]:
                countries_for_classif.append(row[country_apply])  # add applier for this classifier on the current row
                """on the next step we make key: (classifier, country, year) to store amount of given patents.
                 So data will be stored in the dictionary where keys represent classifier, applier-country and 
                 year of getting patent and values represent amount of patents for their keys. 
                 Hereafter values of the dictionary will be accessed by keys to fill cells of resulting table"""
                key = (classifier, row[country_apply], row[year_apply])
                years_counts[key] = years_counts[key] + 1 if key in years_counts else 1
        all_countries_for_classifs.append(list(set(countries_for_classif)))

    tuples = []  # list of tuples (classifier, country) multiindex to be made of
    for i in range(len(unique_clsf_splited)):
        clsfr = unique_clsf_splited[i]
        countries = all_countries_for_classifs[i]  # 2d array
        for country in countries:
            tuples.append((clsfr, country))
    ind = pd.MultiIndex.from_tuples(tuples, names=[c2, c3])
    cols = pd.MultiIndex.from_product([[c1], [i for i in years]])
    df64 = pd.DataFrame(0, index=ind, columns=cols)
    for key in years_counts:  # filling resulting dataframe with values from dictionary
        df64.loc[(key[0], key[1]), (c1, int(key[2]))] = years_counts[key]
    non_zero_rows = df64.any(axis=1)
    df_6_4 = df64[non_zero_rows]
    return df_6_4


def gen_df_for_6_5_table(mdf):
    # Table 6.5 (mutual patenting activity) generation

    # storing column names, which are used in this function
    c1 = 'Страна заявитель'
    c2 = 'Страна выдачи'
    c3 = 'Страна патентования'
    c4 = 'Количество патентов'
    c5 = 'Национальных \nпатентов'
    c6 = 'Запатентовано \nв других \nстранах'
    c7 = 'Национальная \nпринадлежность \nзаявителя'
    c8 = 'Всего'
    c9 = 'Итого'

    publisher_countries = mdf[c2].unique()  # s_otrs
    applicant_countries = mdf[c1].unique()  # s_apcts
    indexes = pd.Series(np.append(applicant_countries, c9))  # making index column for resulting df (df_6_5) ind_s
    for_ind_iterate_list = []
    for country in publisher_countries:
        for_ind_iterate_list.append([c3, country])
    for_ind_iterate_list.append([c4, c5])
    for_ind_iterate_list.append([c4, c6])
    column_names = pd.MultiIndex.from_frame(pd.DataFrame(for_ind_iterate_list), names=[' ', c7])
    df_6_5 = pd.DataFrame(0, columns=column_names, index=indexes)
    df_6_5[c8] = [0 for _ in range(0, indexes.shape[0])]

    df_mp = pd.DataFrame(pd.concat([mdf[c1], mdf[c2]], axis=1))
    df_v = df_mp.groupby([country_apply, country_gave]).aggregate({country_gave: 'count'})

    for appl in applicant_countries:
        for outr in publisher_countries:
            if (appl, outr) in df_v.index:
                val = df_v.loc[(appl, outr)].values
                df_6_5.loc[appl, (c3, outr)] = val
                if appl == outr:
                    df_6_5.loc[appl, (c4, c5)] += val
                else:
                    df_6_5.loc[appl, (c4, c6)] += val
                df_6_5.loc[appl, c8] = df_6_5.loc[appl, (c4, c5)] + df_6_5.loc[appl, (c4, c6)]

    for outr in publisher_countries:
        df_6_5.loc[c9, (c3, outr)] = df_6_5[(c3, outr)].sum()

    df_6_5.loc[c9, (c4, c5)] = df_6_5[(c4, c5)].sum()
    df_6_5.loc[c9, (c4, c6)] = df_6_5[(c4, c6)].sum()
    df_6_5.loc[c9, c8] = df_6_5[c8].sum()

    return df_6_5


def gen_df_for_6_6_table(mdf):
    # Table 6.6 (The geography of patenting...) generation

    # storing column names, which are used in this function
    c1 = 'Наименование фирмы-патентовладельца'
    c2 = 'Наименование технического решения (изобретения)'
    c3 = 'Номер первичной заявки'
    c4 = 'Дата приоритета'
    c5 = 'Дата публикации первичной заявки'
    c7 = 'Номера выданных патентов (поданных заявок) по странам выдачи'
    countries_first_ind = find_index_of_first_country(mdf)
    columns_first_part = pd.MultiIndex.from_product([[c1, c2, c3, c4, c5], [' ']])

    mdf[prior_date] = pd.to_datetime(mdf[prior_date]).dt.strftime('%d.%m.%Y')
    mdf[publish_date] = pd.to_datetime(mdf[publish_date]).dt.strftime('%d.%m.%Y')

    df_first_part = pd.concat(
        [
            mdf[applr],
            mdf[invention],
            mdf[applctn_num],
            mdf[prior_date],
            mdf[publish_date]
        ],
        axis=1
    )

    df_first_part.columns = columns_first_part
    columns_second_part = pd.MultiIndex.from_product([[c7], mdf.iloc[::, countries_first_ind::].columns])
    df_second_part = mdf.iloc[::, countries_first_ind::]
    df_second_part.columns = columns_second_part
    return pd.concat([df_first_part, df_second_part], axis=1)


def export_df(df, ext, table_num):
    ind_bool = False if table_num == '61' else True
    if ext == 'xlsx':
        df.to_excel('OUT' + table_num + '.' + ext, index=ind_bool)
        return 0
    elif ext == 'csv':
        df.to_csv('OUT' + table_num + '.' + ext, index=ind_bool, encoding='utf8')
        return 0


def main():
    parser = argparse.ArgumentParser(description="Script generates subtables")
    parser.add_argument("pathtofile", help="Enter path to file")
    parser.add_argument("-of", "--outformat", help="Enter output files' format")
    args = parser.parse_args()

    path = args.pathtofile
    output_data_format = args.outformat
    input_data_format = path.split('.')[1]
    if output_data_format is None:
        output_data_format = input_data_format

    supported_formats = ['xlsx', 'ods', 'csv']

    if not ((input_data_format in supported_formats) and (output_data_format in supported_formats)):
        print("Script works with XLSX, CSV and ODS formats only")
        return 0

    data = extract_data(path)[0]
    export_df(gen_df_for_6_1_table(data), output_data_format, '61')
    export_df(gen_df_for_6_4_table(data), output_data_format, '64')
    export_df(gen_df_for_6_5_table(data), output_data_format, '65')
    export_df(gen_df_for_6_6_table(data), output_data_format, '66')
    return 0


if __name__ == '__main__':
    main()
