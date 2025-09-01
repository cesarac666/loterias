class FiltroDezenasParesImpares:
    def __init__(self, dezenas_pares=None, dezenas_impares=None, ativo=True):
        self.ativo = ativo
        self.dezenas_pares = set(dezenas_pares or [])
        self.dezenas_impares = set(dezenas_impares or [])

    def apply(self, rows):
        if not self.ativo:
            return list(rows)
        filtrados = []
        for r in rows:
            dezenas = [r[f'n{i}'] for i in range(1, 16)]
            par = sum(1 for d in dezenas if d % 2 == 0)
            impar = len(dezenas) - par
            if (not self.dezenas_pares or par in self.dezenas_pares) \
               and (not self.dezenas_impares or impar in self.dezenas_impares):
                filtrados.append(r)
        return filtrados


class FiltroTresPorLinha:
    def __init__(self, ativo=True):
        self.ativo = ativo

    def apply(self, rows):
        if not self.ativo:
            return list(rows)
        filtrados = []
        for r in rows:
            dezenas = [r[f'n{i}'] for i in range(1, 16)]
            linhas = [0] * 5
            for d in dezenas:
                linhas[(d - 1) // 5] += 1
            if all(l == 3 for l in linhas):
                filtrados.append(r)
        return filtrados
