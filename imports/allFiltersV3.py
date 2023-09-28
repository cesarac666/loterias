import pandas as pd

class Filtro(object):
    def __init__(self, ativo):
        self.ativo = ativo

    def apply(self, df):
        raise NotImplementedError('Subclass must implement abstract method')

class FiltroResultadosAnteriores(Filtro):
    def __init__(self, dfFiltrado, dfResultados, ativo=True):
        super().__init__(ativo)
        self.dfFiltrado = dfFiltrado
        self.dfResultados = dfResultados

    def apply(self, df):
        indice = pd.DataFrame(self.dfFiltrado['CC'] - 1, columns=['CC'])  # Convertemos a série para um DataFrame
        dfRAnteriores = pd.merge(indice, self.dfResultados, on='CC', how='inner')  # Realizamos o merge com base na coluna 'CC'
        # dfRAnteriores['CCOriginal'] = dfRAnteriores['CC']+1
        dfRAnteriores = dfRAnteriores.assign(CCOriginal = dfRAnteriores['CC']+1)
        return dfRAnteriores

class FiltroQuaseTresPorLinha(Filtro):
    def __init__(self, ativo=True):
        super().__init__(ativo)

    def apply(self, df):
        if self.ativo:
            def is_quasi_three_per_line(pattern):
                # Contando o número de ocorrências de cada valor
                counts = {i: pattern.count(i) for i in pattern}
                # Verificando se o padrão atende ao critério
                return counts.get(3, 0) == 3 and counts.get(2, 0) == 1 and counts.get(4, 0) == 1

            # Filtrando o DataFrame
            return df[df['countL'].apply(is_quasi_three_per_line)]
        else:
            return df

# VERSAO FIXA >>> 3 2/4 3 2/4 3 
class FiltroQuaseTresPorLinhaFixo(Filtro):
    def __init__(self, ativo=True):
        super().__init__(ativo)

    def apply(self, df):
        if self.ativo:
            def is_quasi_three_per_line(pattern):
                # Contando o número de ocorrências de cada valor
                counts = {i: pattern.count(i) for i in pattern}
                # Verificando se o padrão atende ao critério
                three_counts = counts.get(3, 0)
                two_counts = counts.get(2, 0)
                four_counts = counts.get(4, 0)
                
                return (three_counts == 3 and two_counts == 1 and four_counts == 1)

            # Filtrando o DataFrame
            return df[df['countL'].apply(is_quasi_three_per_line)]
        else:
            return df


class FiltroTresPorLinha(Filtro):
    def __init__(self, ativo=True):
        super().__init__(ativo)

    def apply(self, df):
        if self.ativo:
            # implementa a lógica de 3 números por linha
            rows = []
            for i, row in df.iterrows():
                # numbers = sorted(row[2:17])
                numbers = {row[f'B{j}'] for j in range(1, 16)}
                lines = [0]*5
                for num in numbers:
                    lines[(num-1)//5] += 1
                if all(line == 3 for line in lines):
                    rows.append(row)
            return pd.DataFrame(rows, columns=df.columns)
        else:
            return df


class FiltroDezenasParesImpares(Filtro):
    def __init__(self, dezenas_pares, dezenas_impares, ativo=True):
        super().__init__(ativo)
        self.dezenas_pares = dezenas_pares
        self.dezenas_impares = dezenas_impares

    def apply(self, df):
        if self.ativo:
            # implementa a lógica de dezenas pares e ímpares
            rows = []
            for i, row in df.iterrows():
                #numbers = row[2:17]
                numbers = {row[f'B{j}'] for j in range(1, 16)}
                par_count = sum(1 for num in numbers if num % 2 == 0)
                impar_count = sum(1 for num in numbers if num % 2 != 0)
                if par_count == self.dezenas_pares and impar_count == self.dezenas_impares:
                    rows.append(row)
            return pd.DataFrame(rows, columns=df.columns)
        else:
            return df

class FiltroDezenaSemColunasSequenciasRepetidas(Filtro):
    def __init__(self, ativo=True):
        super().__init__(ativo)

    def apply(self, df):
        if self.ativo:
            rows = []
            for i, row in df.iterrows():
                if row['countCRE'] == 0:
                    rows.append(row)
            return pd.DataFrame(rows, columns=df.columns)
        else:
            return df

class FiltroApostasN(Filtro):
    def __init__(self, ativo=True):
        super().__init__(ativo)

    def apply(self, df, num_rows, seed):
        if self.ativo:
          if len(df) < num_rows:
             raise ValueError(f"The DataFrame only has {len(df)} rows, which is less than {num_rows}.")
          else:
             return df.sample(n=num_rows, random_state=seed)
        else:
            return df

class FiltroFrequenciaDezenas(Filtro):
    def __init__(self, g1_count, g2_count, g3_count, g4_count, ativo=True):
        super().__init__(ativo)
        self.g1_count = g1_count
        self.g2_count = g2_count
        self.g3_count = g3_count
        self.g4_count = g4_count

    def apply(self, df):
        if self.ativo:
            # implementa a lógica de contagem de frequência de dezenas
            rows = []
            for i, row in df.iterrows():
                if (len(row['G1']) == self.g1_count and
                    len(row['G2']) == self.g2_count and
                    len(row['G3']) == self.g3_count and
                    len(row['G4']) == self.g4_count):
                    rows.append(row)
            return pd.DataFrame(rows, columns=df.columns)
        else:
            return df

class FiltraApostasNAH(Filtro):
    def __init__(self, ultimo, n_count, a_count, h_count, ativo=True):
        super().__init__(ativo)
        self.ultimo_resultado = ultimo
        self.n = n_count
        self.a = a_count
        self.h = h_count
        #self.apostas_geradas = dfApostas

    def apply(self, dfApostas):
        # implementa a lógica de dezenas pares e ímpares
        rows = []
        countN = 0
        countA = 0
        countH = 0
        for i, row in dfApostas.iterrows():
            numbers = {row[f'B{j}'] for j in range(1, 16)}
            countN = sum(1 for num in numbers if num  in self.ultimo_resultado.NS_to_N)
            countA = sum(1 for num in numbers if num  in self.ultimo_resultado.N_to_A)
            countH = sum(1 for num in numbers if num  in self.ultimo_resultado.AH_to_H)

            if countN == self.n and countA == self.a and countH == self.h:
                rows.append(row)
        return pd.DataFrame(rows, columns=dfApostas.columns)


class ResultadosFiltrados(object):
    def __init__(self, dataframe, filtros):
        self.df = dataframe
        self.filtros = filtros

    def get_filtered_results(self):
        df_filtrado = self.df
        for filtro in self.filtros:
            df_filtrado = filtro.apply(df_filtrado)
        return df_filtrado
