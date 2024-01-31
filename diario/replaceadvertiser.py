import pandas as pd
from relacaoblocoportal import parceiros #importação do dicionário contendo a relação de substituição entre bloco de anuncios e o portal

def formatar_data(df, coluna_data):
    # Converter a coluna para o tipo datetime
    df[coluna_data] = pd.to_datetime(df[coluna_data])

    # Formatar a data no formato desejado (dd/MM/yyyy)
    df[coluna_data] = df[coluna_data].dt.strftime('%d/%m/%Y')

    return df

#Calcular receita líquida a partir da receita bruta
def calcular_receitaliq(df, coluna_receita, coluna_liquida,index):
    #Os valores que vêm no formato xlxs dividem a parte inteira da decimal com vírgula, então é necessário
    #fazer um replace na string para permitir a transformação em número, além de tirar o símbolo de moeda.
    recbruta = df.at[index, coluna_receita].replace(',','.')
    recbruta = float(recbruta[2:])

    #a variavel 'liquida' calcula os 60% da receita bruta.
    liquida= recbruta*0.60
    liquida = round(liquida,4) #limita a 4 casas decimais

    #como trbalharemos geralmente em planilhas, é necessário retrocar as vírgulas por pontos,
    #agora com os valores procurados
    liquida = str(liquida)
    df.at[index, coluna_liquida] = liquida.replace('.',',')
    return df

def calcular_ecpm(df, coluna_receita, coluna_ecpm, index):
    #Os valores que vêm no formato xlxs dividem a parte inteira da decimal com vírgula, então é necessário
    #fazer um replace na string para permitir a transformação em número, além de tirar o símbolo de moeda.
    recbruta = df.at[index, coluna_receita].replace(',','.')
    recbruta = float(recbruta[2:]) 

    #a variavel 'liquida' recebe o valor armazenado na coluna de impressões e o transforma em inteiro para
    #permitir cálculos
    impressoes = int(df.at[index,'Total de impressões'])

    #o eCPM é calculado dividindo a receita bruta pelas impressões e multiplicando por mil
    ecpm = (recbruta / impressoes)*1000
    ecpm = round(ecpm, 4) #limita a 4 casas decimais

    #como trbalharemos geralmente em planilhas, é necessário retrocar as vírgulas por pontos,
    #agora com os valores procurados
    ecpm = str(ecpm)
    df.at[index, coluna_ecpm] = ecpm.replace('.',',')
    return df

def diaemes():
    ontem = str(pd.Timestamp.now() - pd.Timedelta(days=1))
    date = ontem.split(' ')[0]
    ano, mes, dia = date.split('-')
    return dia, mes

dia, mes = diaemes()

# Carregar os dados do arquivo CSV da pasta de entrada
df = pd.read_csv(f"../relatorios_in/Relatório de Acompanhamento NE 10 (01_{mes}_2024 - {dia}_{mes}_2024).xlsx - Dados do Relatório.csv", header=0, sep=",")

#Excluir as colunas 'ID do anunciante' e 'ID do bloco de anúncios'
df = df.drop(['ID do anunciante','ID do bloco de anúncios'], axis=1)

# Chamar a função para formatar a coluna 'Data'
df = formatar_data(df, 'Data')

data_escolhida = f'{dia}/{mes}/2024'
df = df[df['Data'] == data_escolhida]

# cria as colunas de receita líquida e eCPM
df.insert(7,'Receita Líquida', ''*df.shape[0])
df.insert(8,'eCPM', ''*df.shape[0])  
# renomeia a coluna de receita bruta
df.rename(columns={'Receita total de CPM e de CPC (R$)': 'Receita Bruta (R$)'}, inplace=True)

for index, row in df.iterrows(): #passa por todas linhas do dataframe e armazena o indice da coluna em 'index'
    if df.at[index, 'Anunciante'] == '-': #trocar onde o Anunciante for '-' por 'Áudio (0x0)'
        df.at[index, 'Anunciante'] = 'Áudio (0x0)'
    elif df.at[index, 'Anunciante'] == 'Total': #quando chegar na linha total, dar um break para calcular o total na mão
        break

    #substituição dos Blocos de anúncios pelo nome do portal correspondente de acordo com o dicionário em 
    #relacaoblocoportal.py
    for portal in parceiros.keys(): 
        if df.at[index, 'Bloco de anúncios'] in parceiros[portal]:
            df.at[index, 'Bloco de anúncios'] = portal
            break # Interromper o loop interno após encontrar a primeira correspondência
    if '.' in df.at[index, 'Receita Bruta (R$)']: #o arquivo xlsx coloca pontos para separar unidade de milhar das centenas, então é necessário tratá-los
        df.at[index, 'Receita Bruta (R$)'] = df.at[index, 'Receita Bruta (R$)'].replace('.','')
    
    df = calcular_receitaliq(df, 'Receita Bruta (R$)', 'Receita Líquida', index) #chama a função para o cálculo da receita líquida
    df = calcular_ecpm(df, 'Receita Bruta (R$)', 'eCPM', index) #chama a função para o cálculo do eCPM

nomerelatorio = f'Acompanhamento_NE10 Diário({dia}-{mes}).csv'
df.to_csv(f'relatorios_out/{nomerelatorio}', index=False)
