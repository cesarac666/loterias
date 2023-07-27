import requests
from requests.exceptions import ConnectTimeout
from bs4 import BeautifulSoup
import pandas as pd
import re

class LotteryScraper:
    def __init__(self, df):
        self.df = df.copy()
        self.last_contest_url = None
        self.soup = None
        self.last_contest_cc = None

    def get_last_contest_url(self, atual=0):
        print("atual <= 0", atual <= 0)
        print(atual)
        if atual <= 0:
          self.last_contest_cc = self.df['CC'].max() + 1
        else:
          self.last_contest_cc = atual + 1

        #print('last_contest_df ={}'.format(last_contest_df))
        self.last_contest_url = 'https://www.loteriaseresultados.com.br/lotofacil/resultado/' + str(self.last_contest_cc)
        print(self.last_contest_url)

    def fetch_data(self):
        if not self.last_contest_url:
            raise Exception("URL is not set. Call get_last_contest_url method before fetch_data.")

        header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        try:
            req = requests.get(self.last_contest_url, headers=header, timeout=60)
            # process the response
        except ConnectTimeout:
            print("A conexão com o servidor expirou. Por favor, verifique sua conexão com a internet e tente novamente mais tarde.")

        if req.status_code != 200:
            print('Requisição inválida!%s', req.status_code)
            return

        print('Requisição bem sucedida!')
        content = req.content

        soup = BeautifulSoup(content, 'html.parser')
        self.soup = soup

        errorOrException = soup.findAll('title')
        print('ErroException=', errorOrException)

        if errorOrException == 'ErrorException':
            print('ErroException')
            return None
        else:
            numbers = soup.find_all('span', class_='white--text font-weight-bold')
            #print(numbers)

            numbers_list = [int(number.text) for number in numbers]
            #print(numbers_list)
            #self.dez = numbers_list
            return numbers_list

    def get_date(self):
        # Aqui deve ser ajustado de acordo com o layout do site
        p_date = self.soup.find("div", {"class": "mt-2"})
        p_date = p_date.find("strong").contents[0]
        #print("p_date=", p_date)
        #self.dt = p_date
        return p_date.text if p_date else None

    def get_winner(self):
        winner = self.soup.find("v-simple-table", {"class": "text-center"})
        winner_string = winner.find("td").contents[0]
        winner = winner_string.get_text()
        #print("winner=", winner)
        #for str_remove in ["<strong>", "</strong>", "acertos"]:
        winner_string = winner.replace("acertos", "").strip()
        return "99" # STOP !!!

    def add_to_dataframe(self):
        numbers_list = self.fetch_data()

        if numbers_list is None:
            print("No numbers to add")
            return
        new_row = {
            "CC": self.last_contest_cc,
            "Data_Sorteio": self.get_date(),
            "B1": numbers_list[0],
            "B2": numbers_list[1],
            "B3": numbers_list[2],
            "B4": numbers_list[3],
            "B5": numbers_list[4],
            "B6": numbers_list[5],
            "B7": numbers_list[6],
            "B8": numbers_list[7],
            "B9": numbers_list[8],
            "B10": numbers_list[9],
            "B11": numbers_list[10],
            "B12": numbers_list[11],
            "B13": numbers_list[12],
            "B14": numbers_list[13],
            "B15": numbers_list[14],
            "Ganhador": self.get_winner()
        }
        # Nao quero mais alterar o dataset original
        # self.df = self.df.append(new_row, ignore_index=True)
        # return(self.df)

        # Quero apenas exibir o resultado atualizado do site
        new_df = pd.DataFrame(new_row, index=[0])
        print(new_df.to_csv(index=False, header=False))

        return new_df
