# py_financas
Py Finanças é um pacote python que abstrai a obtenção de dados a partir do sistema financeiro brasileiro,
incluindo cálculo de vários impostos

## Indices, Indicadores e Indexadores
Indices, indicadores e indexadores são considerados neste pacote como sinônimos, e todos os dados são obtidos diretamente
a partir dos webservices do [Sistema Gerenciador de Séries Temporais do Banco Central do Brasil[(https://www3.bcb.gov.br),
um sistema público mantido pelo orgão do governo brasileiro, no qual não é necessário criar usuário e senha para recuperar
dados.

SERÁ NECESSÁRIO CONEXÃO COM A INTERNET PARA A RECUPERAÇÃO DE DADOS DE INDICES, UMA VEZ QUE OS MESMOS SÃO OBTIDOS A
PARTIR DE UM WEBSERVICE

```python
import datetime
import py_financas

# As datas de inicio e fim da busca devem ser objetos DateTime, sem necessidade de especificar o fuso horario.
# O fuso horario sempre sera assumido como o Horario Python de Sao Paulo (America/Sao_Paulo)
data_inicio_busca = datetime.datetime.strptime('01/01/2014', '%d/%m/%Y')
data_fim_busca = datetime.datetime.strptime('10/01/2014', '%d/%m/%Y')

# Todos os dados de indices sao recuperados no formato Pandas Dataframe
df = py_financas.indices.recupera_indice(

    # Voce pode selecionar qualquer quantidade de indices para recuperar, com seus nomes escritos de varias formas
    ['indice geral de precos do mercado',
     'taxa selic',
     'dollar',
     'euro',
     'IBOVESPA',
     'NASDAQ',
     'di de um dia'],

    # As datas de inicio da busca da serie temporal devem ser objetos DateTime
    data_inicio_busca,
    data_fim_busca
)

print(df)

#             indice GERAL de precos do mercado  taxa selic  dollar    euro  IBOVESPA  NASDAQ  di de um dia
# 2014-01-01                               0.48         NaN     NaN     NaN       NaN     NaN           NaN
# 2014-01-02                                NaN    0.037468  2.3969  3.2703   50341.0  4143.0      0.036998
# 2014-01-03                                NaN    0.037468  2.3734  3.2300   50981.0  4132.0      0.036998
# 2014-01-06                                NaN    0.037468  2.3783  3.2385   50973.0  4114.0      0.036998
# 2014-01-07                                NaN    0.037468  2.3628  3.2184   50430.0  4153.0      0.036998
# 2014-01-08                                NaN    0.037468  2.3773  3.2329   50576.0  4166.0      0.036998
# 2014-01-09                                NaN    0.037468  2.3954  3.2508   49321.0  4156.0      0.036998
# 2014-01-10                                NaN    0.037468  2.3813  3.2564   49696.0  4175.0      0.036998

# Os titulos das colunas do DataFrame sao iguais aos nomes dos indices buscados
# O valor do IGM-M (Indice Geral de Precos - Mercado) somente e divulgado no primeiro dia de cada mes.

# O mesmo DataFrame acima, com uma nomeclatura e ordenacao de colunas diferente:
df_normal = py_financas.indices.recupera_indice(
    ['IGP-M',
     'SELIC',
     'CDI',
     'USD',
     'EUR',
     'IBOVESPA',
     'NASDAQ'],
    data_inicio_busca,
    data_fim_busca
)
print(df_normal)

#             IGP-M     SELIC       CDI     USD     EUR  IBOVESPA  NASDAQ
# 2014-01-01   0.48       NaN       NaN     NaN     NaN       NaN     NaN
# 2014-01-02    NaN  0.037468  0.036998  2.3969  3.2703   50341.0  4143.0
# 2014-01-03    NaN  0.037468  0.036998  2.3734  3.2300   50981.0  4132.0
# 2014-01-06    NaN  0.037468  0.036998  2.3783  3.2385   50973.0  4114.0
# 2014-01-07    NaN  0.037468  0.036998  2.3628  3.2184   50430.0  4153.0
# 2014-01-08    NaN  0.037468  0.036998  2.3773  3.2329   50576.0  4166.0
# 2014-01-09    NaN  0.037468  0.036998  2.3954  3.2508   49321.0  4156.0
# 2014-01-10    NaN  0.037468  0.036998  2.3813  3.2564   49696.0  4175.0
```

