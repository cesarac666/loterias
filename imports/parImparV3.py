import pandas as pd

class ParImpar:
    def __init__(self):
        self.dataframe = None

    # Função para contar a ocorrência de cada grupo em uma linha
    def getFrequencyResults(self):
      self.dataframe['combPI'] = self.dataframe[['countP', 'countI']].apply(tuple, axis=1)
      combinações_frequentes = self.dataframe['combPI'].value_counts()
      combinações_top = combinações_frequentes.head(10)
      return(combinações_top)

    def calculate_pi(self, df):
        # implementa a lógica de dezenas pares e ímpares
        rows = []
        for i, row in df.iterrows():
            #numbers = row[2:17]
            numbers = {row[f'B{j}'] for j in range(1, 16)}
            par_count = sum(1 for num in numbers if num % 2 == 0)
            impar_count = sum(1 for num in numbers if num % 2 != 0)
            #if par_count == self.dezenas_pares and impar_count == self.dezenas_impares:
            #    rows.append(row)
            self.dataframe.loc[i, 'countP'] = par_count
            self.dataframe.loc[i, 'countI'] = impar_count

        return self.dataframe

