# py_financas
Py Finanças é um pacote python que simplifica obtenção e uso de dados do sistema financeiro brasileiro.

Permite coletar dados do sistema de séries temporais do Banco Central do Brasil, dos Fundos de Investimento regulados pela Comissão de Valores Mobiliários (CVM) e processar informações de Notas de Corretagem/Negociação em Bolsa de Valores/B3.


## Notas de corretagem no formato SINACOR

O [Sistema Integrado de Administração de Corretoras (SINACOR)](https://www.b3.com.br/pt_br/solucoes/plataformas/middle-e-backoffice/sinacor/sobre-o-sinacor/) é uma plataforma presente em 95% das corretoras do Brasil, que simplifica e padroniza a comunicação entre corretoras e investidores.

O pacote py_financas permite a leitura de notas de corretagem em arquivos PDF, contanto que estejam no formato SINACOR.
Para obter seu histórico de notas de corretagem no formato SINACOR, entre em contato com sua corretora e peça, explicitamente, para que enviem seu histórico de notas de corretagem no formato SINACOR, em um ou mais arquivos PDF.


### Parsing de Notas de Corretagem

Parsing é o processo de ler dados em formatos de difícil acesso, e obter resultados que podem ser tratados mais facilmente.
Os arquivos PDF com notas de negociação no formato SINACOR são lidos e processados pelo pacote py_financas, e os resultados são retornados em uma lista de objetos NotaCorretagem.

```python
from py_financas.sinacor import parse_notas_corretagem

lista_arquivos_pdf = ['Insira aqui seus arquivos PDF de notas de corretagem no formato SINACOR.pdf']

objetos_nota_corretagem = parse_notas_corretagem(lista_arquivos_pdf)
```


Um Objeto NotaCorretagem contém informações sobre uma nota de corretagem, incluindo seus impostos, custos, corretora e operações realizadas.


```python
from py_financas import NotaCorretagem
```


### Parsing automático de Posições

Posições são conjuntos de ações do mesmo título, caracterizadas pela quantidade e pelo valor médio de compra das ações ao longo do tempo.
O objeto Posicao pode ser gerado a partir de objetos NotaCorretagem


```python
from py_financas.sinacor import parse_notas_corretagem
from py_financas.sinacor import parse_posicoes_de_notas_de_corretagem

objetos_nota_corretagem = parse_notas_corretagem(lista_arquivos_pdf)

posicoes = parse_posicoes_de_notas_de_corretagem(objetos_nota_corretagem)

for pos in posicoes:
    print(pos.sumario())
```


### Parsing Híbrido de Posições

Por vezes, posições podem requerer informações que não estão presentes nas notas de corretagem, como por exemplo Ofertas Públicas, Subscrições e Desdobramentos (Stock Splits).
Por isso, pode ser necessário inserir operações manuais para completar as informações de uma posição.

O pacote py_financas pode combinar informações de notas de corretagem com informações manuais para gerar um relatório completo de posições.

*As informações manuais devem ser inseridas por meio de arquivos Excel, no formato exato do* [modelo anexo](https://www.google.com)

```python
from py_financas.sinacor import parse_posicoes

lista_arquivos_pdf = ['Insira aqui seus arquivos PDF de notas de corretagem no formato SINACOR.pdf']
lista_arquivos_excel = ['Insira aqui seus arquivos EXCEL de operações manuais no formato do template fornecido.xlsx']

posicoes = parse_posicoes(lista_arquivos_pdf, lista_arquivos_excel)

for pos in posicoes:
    print(pos.sumario())
```



## Indices, Indicadores e Indexadores
Indices, indicadores e indexadores são considerados neste pacote como sinônimos, e todos os dados são obtidos diretamente
a partir dos webservices do [Sistema Gerenciador de Séries Temporais do Banco Central do Brasil](https://www3.bcb.gov.br),
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

