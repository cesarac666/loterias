import pandas as pd

class LotteryAnalyzer:
    def __init__(self, df):
        self.df_original = df.copy()
        self.df  = df
        self.lines = [[1,2,3,4,5], [6,7,8,9,10], [11,12,13,14,15], [16,17,18,19,20], [21,22,23,24,25]]
        self.columns = [[1,6,11,16,21], [2,7,12,17,22], [3,8,13,18,23], [4,9,14,19,24], [5,10,15,20,25]]
        self.count_per_line()
        self.count_per_column()
        self.map_to_positions()
        self.count_row_equals()

    def count_per_line(self):
        self.df['countL'] = self.df.apply(lambda row: [sum(1 for i in range(1,16) if row[f'B{i}'] in line) for line in self.lines], axis=1)

    def count_per_column(self):
        self.df['countC'] = self.df.apply(lambda row: [sum(1 for i in range(1,16) if row[f'B{i}'] in column) for column in self.columns], axis=1)

    def map_to_positions(self):
        position_df = pd.DataFrame()
        for i in range(1, 16):
            position_df[f'P{i}'] = self.df.apply(lambda row: f'a{self.lines.index([n for n in self.lines if row[f"B{i}"] in n][0])+1}{self.columns.index([n for n in self.columns if row[f"B{i}"] in n][0])+1}', axis=1)
        self.df = pd.concat([self.df, position_df], axis=1)

    def count_row_equals(self):
        def count_equal_rows(row):
            # Create a list of lists, where each inner list contains the column positions of the numbers in a row
            row_positions = [[int(row[f'P{i}'][2]) for i in range(1, 16) if int(row[f'P{i}'][1]) == j+1] for j in range(5)]

            # Sort each inner list
            row_positions = [sorted(position) for position in row_positions]

            # Count the number of consecutive rows that have the same column positions
            count = sum(1 for i in range(4) if row_positions[i] == row_positions[i+1])

            return count

        self.df['countCRE'] = self.df.apply(count_equal_rows, axis=1)

    # Função para contar a ocorrência de cada grupo em uma linha
    def getFrequencyColumn(self, head=10):
      #self.df['combPI'] = self.df[['countP', 'countI']].apply(tuple, axis=1)
      combinações_frequentes = self.df['countC'].value_counts()
      combinações_top = combinações_frequentes.head(head)
      return(combinações_top)

