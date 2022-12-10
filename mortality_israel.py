import pandas as pd
import numpy as np
from pandas import Timestamp
import matplotlib.pyplot as plt


class MortalityIsrael:
    """
    Process CBS data of mortality in Israel
    """
    def __init__(self, age_start, age_end):
        """
        Initializes MortalityIsrael to create and plot dataset: (date | number of deaths) for the specified age range
        :param age_start: (int)
        :param age_end: (int)
        """
        self.age_start = age_start
        self.age_end = age_end
        self.age_categ = (
            '0-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74',
            '75-79', '80-84', '85-89')
        return

    def _resave_population_data(self):
        """
        Saves population data in a cut version.
        There is no data for 2020, 2021, the data for these years are replaced by the data for 2019.
        """
        population = pd.DataFrame(columns=['year'] + list(range(1, 90)))
        for year in range(2008, 2020):
            table_data = pd.read_excel('data_israel/population.xlsx', sheet_name=str(year), skiprows=10)
            a = []
            for i in range(1, 90):
                a.append(table_data[i][0])
            population = population.append(pd.DataFrame([[year] + a], columns=['year'] + list(range(1, 90))),
                                           ignore_index=True)
        population = population.append(pd.DataFrame([[2020] + a], columns=['year'] + list(range(1, 90))),
                                       ignore_index=True)
        population = population.append(pd.DataFrame([[2021] + a], columns=['year'] + list(range(1, 90))),
                                       ignore_index=True)
        population = population.append(pd.DataFrame([[2022] + a], columns=['year'] + list(range(1, 90))),
                                       ignore_index=True)
        population.to_csv('data_israel/population_cut.csv', index=False)
        return

    def get_population_year(self):
        """
        Creates DataFrame of population over years
        :return: DataFrame year | population | relative coefficient
        """
        population_table = pd.read_csv('data_israel/population_2008_2022.csv')
        population = {}
        for k in range(len(population_table)):
            population_in_year = 0
            for i in range(self.age_start, self.age_end+1):
                population_in_year = population_in_year + population_table[str(i)][k]
            population[population_table['year'][k]] = population_in_year

        df_population = pd.DataFrame({'year': population.keys(), 'population': population.values()})
        df_population['coef'] = df_population['population']/np.max(df_population['population'])
        self.df_population = df_population
        return df_population

    def get_date_death_by_age(self):
        """
        Creates DataFrame date | number of deaths for the specified age group
        :return: DataFrame date | death
        """
        # import death_date data for 2010-2021 by age (choose from age_categ, not 0-19)
        df_date_death = pd.DataFrame(columns=['date', 'death'])
        age_start_index = int((self.age_start-15)/5)
        age_end_index = int((self.age_end+1-15)/5)-1
        for year in range(2010, 2023, 1):
            table_data = pd.read_excel('data_israel/death_data_by_day_of_death_include_only_deaths_of_residents_of_Israel_in_Israel.xlsx', sheet_name=str(year), skiprows=10)
            death_sum = table_data[self.age_categ[age_start_index]][1:]
            for i in range(age_start_index+1, age_end_index+1):
                death_sum = death_sum + table_data[self.age_categ[i]][1:]
            df = pd.DataFrame({'date': table_data.iloc[1:, 0], 'death': death_sum})
            df_date_death = pd.concat([df_date_death, df], ignore_index=True)

        df_date_death.dropna(inplace=True)
        df_date_death = df_date_death[::-1]
        df_date_death = df_date_death.reset_index(drop=True)
        self.df_date_death = df_date_death
        return df_date_death

    def get_death_in_period_over_years(self, start_date, end_date, year_start, year_end):
        """
        Creates DataFrame number of deaths in the specified period for the specified age range over the years
        :param start_date: (str) date format: '-02-01'
        :param end_date: (str) date format: '-03-29'
        :param year_start: (int)
        :param year_end: (int)
        :return: DataFrame year | death
        """
        death_period_lst = np.array([])
        year_lst = np.array([])
        for year in range(year_start, year_end+1, 1):
            death_period = self.df_date_death.loc[(self.df_date_death['date'] >= Timestamp(str(year)+start_date)) & (self.df_date_death['date'] <= Timestamp(str(year)+end_date))]['death'].sum()
            death_period_lst = np.append(death_period_lst, death_period)
            year_lst = np.append(year_lst, year)
        df_death_in_period = pd.DataFrame({'year': year_lst, 'death_in_period': death_period_lst})
        return df_death_in_period

    def _normalization_by_population(self, df_death_in_period, year_start, year_end):
        """
        Normalizes the number of deaths by population in the specified period
        :param df_death_in_period: (pd.Series) input vector of number of deaths
        :param year_start: (int)
        :param year_end: (int)
        :return: (pd.Series) normalized number of deaths
        """
        coef_normalization = self.df_population[(year_start <= self.df_population['year']) & (self.df_population['year'] <= year_end)]['coef']
        coef_normalization = coef_normalization.reset_index(drop=True)
        df_death_in_period_normalized = df_death_in_period['death_in_period'] / coef_normalization
        return df_death_in_period_normalized

    def plot_death_in_period_over_years(self, start_date, end_date, year_start, year_end, norm=True):
        """
        Plots number of deaths in the specified period for the specified age range over the years
        :param start_date: (str) date format: '-02-01'
        :param end_date: (str) date format: '-03-29'
        :param year_start: (int)
        :param year_end: (int)
        :param norm: (boolean) normalize by population in group if True
        :return: (fig, ax) figure
        """
        df_death_in_period = self.get_death_in_period_over_years(start_date, end_date, year_start, year_end)
        if norm:
            df_death_in_period['death_in_period'] = self._normalization_by_population(df_death_in_period, year_start, year_end)
        fig, ax = plt.subplots()
        ax.bar(df_death_in_period['year'], df_death_in_period['death_in_period'], width=0.2, color='b')

        mean_death_in_period = df_death_in_period['death_in_period'].mean()
        std_death_in_period = df_death_in_period['death_in_period'].std()

        ax.axhspan(mean_death_in_period - std_death_in_period, mean_death_in_period + std_death_in_period,
                   alpha=0.3, color='k', label='$\mathrm{\sigma}$')
        ax.axhspan(mean_death_in_period - 2 * std_death_in_period, mean_death_in_period + 2 * std_death_in_period,
                   alpha=0.3, color='r', label='$\mathrm{2*\sigma}$')
        ax.axhline(y=mean_death_in_period, linestyle='--', color='k')

        lim_bottom = mean_death_in_period - 4 * std_death_in_period
        if lim_bottom < 0: lim_bottom = 0
        lim_top = mean_death_in_period + 4 * std_death_in_period
        ax.set_ylim(bottom=lim_bottom, top=lim_top)

        ax.set_ylabel('normalized death') if norm else ax.set_ylabel('death')
        plt.xticks(rotation=90)

        start_date_month = Timestamp('2022' + start_date).month_name()
        start_date_day = str(Timestamp('2022' + start_date).day)
        end_date_month = Timestamp('2022' + end_date).month_name()
        end_date_day = str(Timestamp('2022' + end_date).day)
        ax.set_title(str(self.age_start) + '-' + str(
             self.age_end) + ' years, between ' + start_date_day + ' ' + start_date_month + ' and ' + end_date_day + ' ' + end_date_month + '. Israel.')
        ax.legend(loc='best')
        fig.tight_layout()
        return fig, ax

    def __plot_average_data(self, norm=True):
        """
        NOT RELEASED
        Plots moving average number of deaths for the specified age group
        :param norm: (boolean)
        :return:
        """
        # basis = 7*8 # days
        # death_lst = np.array([]); date_lst = np.array([]);
        # for i in range(int(len(date_death)/basis)):
        #     death_lst = np.append(death_lst, date_death['death'][i*basis:(i+1)*basis].sum())
        #     date_lst = np.append(date_lst, date_death['date'][i*basis]-datetime.timedelta(days=int(basis/2)))
        # fig, ax = plt.subplots()
        # if norm:
        #     for i in range(len(date_lst)):
        #         ax.bar(date_lst[i], death_lst[i]/population[date_lst[i].year], color='b', width = 20)
        #         ax.set_ylabel('normalized death')
        # else:
        #         ax.bar(date_lst, death_lst, color='b', width = 20)
        #         ax.set_ylabel('death')
        # plt.xticks(rotation=90)
        # ax.set_title('20-29 years, 8 weeks averaged ')
        # fig.tight_layout()
        return

    def __population_interpolation(self):
        """
        # NOT RELEASED
        :return:
        """
        # x = list(population.keys())[:-2]
        # y = list(population.values())[:-2]
        # fit = np.polyfit(x, y, 2)
        # plt.plot(x, y, marker='o')
        # plt.plot(x, np.polyval(fit, x))
        return


# obj = MortalityIsrael(age_start=20, age_end=34)
# obj.get_population_year()
# obj.get_date_death_by_age()
# fig, ax = obj.plot_death_in_period_over_years('-02-01', '-03-29', 2015, 2022, norm=True)
