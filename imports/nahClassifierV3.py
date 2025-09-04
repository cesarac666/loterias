class NahClassifier:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    # Função para contar a ocorrência de cada grupo em uma linha
    def getNahResults(self):
      self.dataframe['combNAH'] = self.dataframe[['countN', 'countA', 'countH']].apply(tuple, axis=1)
      combinações_frequentes = self.dataframe['combNAH'].value_counts()
      combinações_top = combinações_frequentes.head(22)
      return(combinações_top)

    def count_combinations(self, df):
        # Agrupa o DataFrame pelas colunas 'combNAH_df1' e 'combNAH_df2' e conta o número de ocorrências
        count_df = df.groupby(['combNAH_df1', 'combNAH_df2']).size().reset_index(name='count')
        count_df = count_df.sort_values('count', ascending=False)
        return count_df

    def find_combinations(self, df, comb):
        # Filtra o DataFrame para incluir apenas as linhas onde 'combNAH_df1' é igual a 'comb'
        filtered_df = df[df['combNAH_df1'] == comb]
        # Ordena o DataFrame filtrado pela coluna 'count' de forma decrescente
        filtered_df = filtered_df.sort_values('count', ascending=False)
        return filtered_df
        
    def merge_dataframes(self, df1, df2, key_col1, key_col2):
        df_merge = pd.merge(df1, df2, left_on=key_col1, right_on=key_col2, suffixes=('_df1', '_df2'))
        return df_merge

    def column_filter(self, df1, colunas):
        df_new = df1[colunas]
        return df_new

    def classify(self):
        self.dataframe['countN'] = 0
        self.dataframe['countA'] = 0
        self.dataframe['countH'] = 0
        self.dataframe['GN'] = None
        self.dataframe['GA'] = None
        self.dataframe['GH'] = None

        for i in range(2, len(self.dataframe)):
            current_draw = {self.dataframe.iloc[i][f'B{j}'] for j in range(1, 16)}
            previous_draw = {self.dataframe.iloc[i-1][f'B{j}'] for j in range(1, 16)}
            two_draws_ago = {self.dataframe.iloc[i-2][f'B{j}'] for j in range(1, 16)}

            N = current_draw - previous_draw
            A = current_draw.intersection(previous_draw) - two_draws_ago
            H = current_draw.intersection(previous_draw).intersection(two_draws_ago)

            self.dataframe.loc[i, 'countN'] = len(N)
            self.dataframe.loc[i, 'countA'] = len(A)
            self.dataframe.loc[i, 'countH'] = len(H)

            self.dataframe.at[i, 'GN'] = sorted(list(N))
            self.dataframe.at[i, 'GA'] = sorted(list(A))
            self.dataframe.at[i, 'GH'] = sorted(list(H))

        return self.dataframe



        
