import pandas as pd
import ast
import random
import math

import pandas as pd
import itertools
import random

from allFiltersV3 import ResultadosFiltrados

class BetGeneratorV2:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def add_bet_columns(self):
        all_numbers = set(range(1, 26))

        for i in self.dataframe.index:
            NS_to_N = all_numbers - set(self.dataframe.loc[i][f'B{j}'] for j in range(1, 16))
            AH_to_H = set(self.dataframe.loc[i, 'GA']).union(set(self.dataframe.loc[i, 'GH']))
            N_to_A = set(self.dataframe.loc[i, 'GN'])

            # Convert the sets to sorted lists and then to strings
            self.dataframe.loc[i, 'NS_to_N'] = str(sorted(list(NS_to_N)))
            self.dataframe.loc[i, 'AH_to_H'] = str(sorted(list(AH_to_H)))
            self.dataframe.loc[i, 'N_to_A'] = str(sorted(list(N_to_A)))

        return self.dataframe

    def generate_bets(self, num_bets=1000):
        bets = pd.DataFrame(columns=['id'] + [f'B{j}' for j in range(1, 16)])

        for i in self.dataframe.index:
            NS_to_N = set(eval(self.dataframe.loc[i, 'NS_to_N']))
            AH_to_H = set(eval(self.dataframe.loc[i, 'AH_to_H']))
            N_to_A = set(eval(self.dataframe.loc[i, 'N_to_A']))

            lencomb = 15
            possible_numbers = list(NS_to_N.union(AH_to_H).union(N_to_A))
            possible_bets = list(itertools.combinations(possible_numbers, lencomb))

            random.shuffle(possible_bets)

            print('LEN possible_bets: ', len(possible_bets))

            for bet_id, bet in enumerate(possible_bets[:num_bets], 1):
                bet_dict = {'id': bet_id}
                for j, number in enumerate(bet, 1):
                    bet_dict[f'B{j}'] = number
                bets = bets.append(bet_dict, ignore_index=True)

        return bets


    def generate_filtered_bets(self, filtros, num_bets):
        print('Iniciando a geracao de apostas com filtros')
        bets = self.generate_bets()  # Generate 1000 bets generics
        print('QTD de apostas geradas(antes):', len(bets))

        filtered_results = ResultadosFiltrados(bets, filtros)  # Create a ResultadosFiltrados object
        filtered_bets = filtered_results.get_filtered_results()  # Get the filtered bets
        print('Encerrando a geracao de apostas com filtros')
        print('QTD de apostas geradas(depois):', len(filtered_bets))

        return filtered_bets

    def generate_exact_filtered_bets(self, filtros, num_bets, max_attempts=100):
        filtered_bets = self.generate_filtered_bets(filtros, num_bets)
        attempt_count = 0
        print('QTD Apostas geradas:',len(filtered_bets))
        print('QTD Total de Apostas a ser gerada:', num_bets)

        while len(filtered_bets) < num_bets and attempt_count < max_attempts:
            print('Iniciando a geracao em loop apostas com filtros')
            print('QTD de apostas que faltam:', num_bets - len(filtered_bets))
            extra_bets = self.generate_filtered_bets(filtros, num_bets - len(filtered_bets))
            print('QTD Apostas extras geradas:',len(extra_bets))
            filtered_bets = pd.concat([filtered_bets, extra_bets])
            attempt_count += 1

        if attempt_count == max_attempts:
          print(f"Warning: Número máximo alcançado. Somente {len(filtered_bets)} apostas foram geradas.")

        print('Encerrando a geracao extra de apostas com filtros')
        return filtered_bets.iloc[:num_bets]

    def generate_bets_nah(self, ultimo, num_bets=1000, n=7, a=4, h=4):
        print('Iniciando a geracao em loop apostas com NAH')
        bets = pd.DataFrame(columns=['id'] + [f'B{j}' for j in range(1, 16)])

        for i in self.dataframe.index:
            NS_to_N = set(eval(self.dataframe.loc[i, 'NS_to_N']))
            AH_to_H = set(eval(self.dataframe.loc[i, 'AH_to_H']))
            N_to_A = set(eval(self.dataframe.loc[i, 'N_to_A']))

            # Calculate and print the total number of possible combinations
            total_combinations = math.comb(len(NS_to_N), n) * math.comb(len(AH_to_H), h) * math.comb(len(N_to_A), a)
            print(f'Total possible combinations: {total_combinations}')

            #print("{0} is an integer while {1} is a string.".format(a,b))
            print('O ultimo resultado tem NS_to_N={0} e seu len é {1}'.format(NS_to_N,len(NS_to_N)))
            print('O ultimo resultado tem  N_to_A={0} e seu len é {1}'.format( N_to_A,len(N_to_A)))
            print('O ultimo resultado tem  AH_to_H={0} e seu len é {1}'.format( AH_to_H,len(AH_to_H)))

            print('len(NS_to_N) < n', len(NS_to_N) < n)
            print(' len(N_to_A) < a',  len(N_to_A) < a)
            print('len(AH_to_H) < h', len(AH_to_H) < h)

            # Check that the sets are large enough
            if len(NS_to_N) < n or len(N_to_A) < a or len(AH_to_H) < h :
              raise ValueError("One of the sets is too small for the requested number of elements")

            for bet_id in range(1, num_bets + 1):
                NS_to_N_numbers = random.sample(NS_to_N, n)
                N_to_A_numbers = random.sample(N_to_A, a)
                AH_to_H_numbers = random.sample(AH_to_H, h)

                bet_numbers = NS_to_N_numbers + N_to_A_numbers + AH_to_H_numbers

                bet_dict = {'id': bet_id}
                for j, number in enumerate(sorted(bet_numbers), 1):
                    bet_dict[f'B{j}'] = number
                bets = bets.append(bet_dict, ignore_index=True)

        return bets


    def calculate_hits(self, result, bets):
        hits = []
        result_copy = self.select_columns(result)
        bets_copy   = self.select_columns(bets)
        result_set = set(result_copy.iloc[0]) # assumindo que 'result' é um DataFrame com uma única linha
        for i in range(len(bets)):
            bet = bets_copy.iloc[i]
            bet_set = set(bet)
            #bet_set = set(element for sublist in bet for element in sublist)
            hit = len(bet_set & result_set)
            hits.append(hit)
        return hits

    def select_columns(self, df_conferir):
        columns = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15']
        return df_conferir[columns].copy()


    def calculate_winnings(self, hits):
        soma = 0.0
        for i in hits:
            if i == 11:
                soma += 6.00
            elif i == 12:
                soma += 12.00
            elif i == 13:
                soma += 30.00
            elif i == 14:
                soma += 1000.00
                print("********** QUASE LÁ *************")
            elif i == 15:
                soma += 1000000.00
                print("********** VENCEDOR *************")
        return soma

