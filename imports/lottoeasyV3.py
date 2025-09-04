import pandas as pd

class LoadData():
    def __init__(self, filepath):
        self.filepath = filepath
        self.dataframe = None

    def read_csv(self,separador=","):
        self.dataframe = pd.read_csv(self.filepath, sep=separador)



        
        
 
