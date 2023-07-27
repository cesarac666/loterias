import pandas as pd

class Frequency:
    def __init__(self):
        self.dataframe = None
        self.frequency_dataframe = None

    # Função para contar a ocorrência de cada grupo em uma linha
    def getFrequencyResults(self):
      self.dataframe['combFreq'] = self.dataframe[['countG1', 'countG2', 'countG3', 'countG4']].apply(tuple, axis=1)
      combinações_frequentes = self.dataframe['combFreq'].value_counts()
      combinações_top = combinações_frequentes.head(10)
      return(combinações_top)

    def calculate_frequency(self):
        # Transforma as colunas em linhas
        melted_df = self.dataframe.melt(value_vars=['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15'])

        # Calcula a frequência de cada número
        frequency = melted_df['value'].value_counts().sort_index()

        # Transforma a Series em DataFrame e renomeia as colunas
        self.frequency_dataframe = frequency.reset_index().rename(columns={'index': 'Dez', 'value': 'Freq'})

        # Calcula a frequência percentual
        total_draws = len(self.dataframe)
        self.frequency_dataframe['Freq Percentual'] = (self.frequency_dataframe['Freq'] / total_draws) * 100

    def create_groups(self):
        # Define a função para classificar os números
        #############################################
        # TERIA QUE TROCAR POR: DIF = MAX(PERC) - MIN(PERC) / 4;
        # MIN + (1*DIF); MIN + (2*DIF);  MIN + (3*DIF);
        def classify(n):
            if n >= 62:
                return 'G1'
            elif n >= 60:
                return 'G2'
            elif n >= 58:
                return 'G3'
            else:
                return 'G4'

        # Aplica a função à coluna de frequência percentual
        self.frequency_dataframe['Grupo'] = self.frequency_dataframe['Freq Percentual'].apply(classify)

        # Cria conjuntos para cada grupo
        self.g1 = set(self.frequency_dataframe[self.frequency_dataframe['Grupo'] == 'G1']['Dez'])
        self.g2 = set(self.frequency_dataframe[self.frequency_dataframe['Grupo'] == 'G2']['Dez'])
        self.g3 = set(self.frequency_dataframe[self.frequency_dataframe['Grupo'] == 'G3']['Dez'])
        self.g4 = set(self.frequency_dataframe[self.frequency_dataframe['Grupo'] == 'G4']['Dez'])

    def add_group_columns_v3(self, df):
      df['G1'] = None
      df['G2'] = None
      df['G3'] = None
      df['G4'] = None
      df['countG1'] = 0
      df['countG2'] = 0
      df['countG3'] = 0
      df['countG4'] = 0
      for i in range(len(df)):
          draws = { df.iloc[i][f'B{j}'] for j in range(1, 16)}
          df.at[i, 'G1'] = sorted(list(draws &  self.g1))
          df.at[i, 'G2'] = sorted(list(draws &  self.g2))
          df.at[i, 'G3'] = sorted(list(draws &  self.g3))
          df.at[i, 'G4'] = sorted(list(draws &  self.g4))
          df.at[i, 'countG1'] = len(draws &  self.g1)
          df.at[i, 'countG2'] = len(draws &  self.g2)
          df.at[i, 'countG3'] = len(draws &  self.g3)
          df.at[i, 'countG4'] = len(draws &  self.g4)
      return  df
