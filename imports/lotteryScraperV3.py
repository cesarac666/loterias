import requests
from requests.exceptions import ConnectTimeout
from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from bs4 import Tag 
from bs4 import BeautifulSoup

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

    # busca de outro site:
    def formatar_dados(self, titulo, data, numeros):
        # Verifique se os argumentos são do tipo correto
        if not isinstance(titulo, (str, Tag)) or not isinstance(data, (str, Tag)):
            raise ValueError("Os argumentos 'titulo' e 'data' devem ser strings ou objetos Tag do Beautiful Soup!")
    
        # Extrair a data do título e formatar para DD/MM/YYYY
        data_bruta = titulo.text if isinstance(titulo, Tag) else titulo
        mes_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        mes, dia, ano = data_bruta.replace(',', '').split()
        data_formatada = f"{int(dia):02}/{mes_map[mes]}/{ano}"
    
        # Extrair o número do sorteio de data
        numero_sorteio = data.text if isinstance(data, Tag) else data
        numero_sorteio = numero_sorteio.replace("Draw ", "").strip()
    
        # Junte tudo
        resultado = f"{numero_sorteio},{data_formatada},{','.join(map(str, numeros))},77"
    
        return resultado

    def retorno_resultado_online_site_novo(self): 
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
        url = "https://www.lotoloto.com.br/lotofacil/"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        # print(soup)
    
        divs_numeros = soup.select('.item.recente .numeros')
        primeira_div = divs_numeros[0]
        div_numeros = primeira_div.select('.num')
    
        div_titulo = soup.select('.item.recente .titulo')
        div_data   = soup.select('.item.recente .data')
        #print("div_data", div_data[0])
        # for numero in div_numeros:
        #    print(numero.text.strip())
        # print(div_numeros)
        numeros = []
        for numero in div_numeros:
            isso = numero.text.strip()
            numeros.append(int(isso))
    
        #print(numeros)
        titulo = div_titulo[0]
        #print("titulo", titulo)
        data   = div_data[0]
        #print("data", data)
        #print(f"Tipo de 'titulo': {type(titulo)}")
        #print(f"Tipo de 'data': {type(data)}")
        
        return self.formatar_dados(titulo, data, numeros)

    def retorna_df_ultimo_resultado(self, atual=3045):
        print("entrou aqui 1")
        # data_str = self.retorno_resultado_online_site_novo()
        data_str = self.retorna_todos_site_novo(atual)
        data_parts = data_str.split(',')
        if data_parts is None:
            print("No numbers to add")
            return
        data_dict = {
            "CC": data_parts[0],
            "Data_Sorteio": data_parts[1],
            "B1": data_parts[2],
            "B2": data_parts[3],
            "B3": data_parts[4],
            "B4": data_parts[5],
            "B5": data_parts[6],
            "B6": data_parts[7],
            "B7": data_parts[8],
            "B8": data_parts[9],
            "B9": data_parts[10],
            "B10": data_parts[11],
            "B11": data_parts[12],
            "B12": data_parts[13],
            "B13": data_parts[14],
            "B14": data_parts[15],
            "B15": data_parts[16],
            "Ganhador": data_parts[17],  # assumindo que "99" é o ganhador
        }
        columns = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15']

        new_df = pd.DataFrame(data_dict, index=[0])
        new_df[columns] = new_df[columns].astype(int)
        
        return new_df
    # fim da busca de outro site

    # aqui é o retorno do site antigo 
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
    
    def retorna_todos_site_novo (self, atual=3045):
        # print("agora vai ...")
        headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
    
        url = "https://www.lotoloto.com.br/sorteios/lotofacil/" + str(atual) + "/"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        # print(soup)
    
        divs_numeros = soup.select('.item.ordem1 .numeros')

        if(divs_numeros is None or len(divs_numeros) <= 0):
            return None
        
        if(divs_numeros is not None and len(divs_numeros) > 0):
            primeira_div = divs_numeros[0]
            div_numeros = primeira_div.select('.num')
    
        div_titulo = soup.select('.item.ordem1 .titulo.fcCor')
        div_data   = soup.select('.item.ordem1 .data')
        #print("div_data", div_data[0])
        # for numero in div_numeros:
        #    print(numero.text.strip())
        # print(div_numeros)
        numeros = []
        for numero in div_numeros:
            isso = numero.text.strip()
            numeros.append(int(isso))
    
        #print(numeros)
        titulo = div_titulo[0]
        #print("titulo", titulo)
        data   = div_data[0]
        #print("data", data)
        #print(f"Tipo de 'titulo': {type(titulo)}")
        #print(f"Tipo de 'data': {type(data)}")

        return self.formatar_dados_novo(titulo, data, numeros)

    def formatar_dados_novo(self, titulo, data, numeros):
        # Simulando os elementos Tag para o exemplo
        # titulo_html = BeautifulSoup('<div class="titulo fcCor"><h3>Concurso 3045</h3></div>', 'html.parser')
        # data_html = BeautifulSoup('<div class="data"> 05/03/2024 </div>', 'html.parser')

        titulo_html = titulo
        data_html = data 
        # Extraindo o texto do título e usando expressões regulares para encontrar o número
        titulo_texto = titulo_html.find('h3').text  # "Concurso 3045"
        numeros_concurso = re.search(r'\d+', titulo_texto)
        if numeros_concurso:
            numero_concurso = numeros_concurso.group(0)  # "3045"

        # Extraindo e limpando a data
        data_texto = data_html.text.strip()  # "05/03/2024"

        #print(f'Número do Concurso: {numero_concurso}')
        #print(f'Data: {data_texto}')
        
        # Junte tudo
        resultado = f"{numero_concurso},{data_texto},{','.join(map(str, numeros))},77"
        return resultado 