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
    recbruta = float(recbruta)

    #a variavel 'liquida' calcula os 60% da receita bruta.
    liquida= recbruta*0.60
    liquida = round(liquida,4) #limita a 4 casas decimais

    #como trbalharemos geralmente em planilhas, é necessário retrocar as vírgulas por pontos,
    #agora com os valores procurados
    liquida = str(liquida).replace('.',',')
    df.at[index, coluna_liquida] = liquida
    return df

def manipuladata():
    hoje = pd.Timestamp.now()
    ontem = str(hoje - pd.Timedelta(days=1))

    nome_hoje = hoje.day_name()
    nome_mes = (hoje - pd.Timedelta(days=1)).month_name()[:3]
    

    date = ontem.split(' ')[0]
    ano, mes, dia = date.split('-')
    if dia[0] == '0':
        title_day = dia[1]
    else:
        title_day = dia
    
    return dia, mes, nome_hoje, nome_mes, title_day

dia, mes, hoje, abbmonth, title_day = manipuladata()

# Carregar os dados do arquivo CSV da pasta de entrada
df = pd.read_csv(f"../relatorios_in/Relatório de Acompanhamento NE 10 ({abbmonth} 1, 2024 - {abbmonth} {title_day}, 2024).xlsx - Report data.csv", header=0, sep=",")

#Excluir as colunas 'ID do Advertiser' e 'ID do Ad unit'
df = df.drop(['Advertiser ID','Ad unit ID'], axis=1)

# Chamar a função para formatar a coluna 'Data'
df = formatar_data(df, 'Date')

if hoje == 'Monday':
    dom, sab, sex = int(dia), int(dia)-1, int(dia)-2
    datas_selecionadas = [f'{dom}/09/2024', f'{sab}/09/2024', f'{sex}/09/2024']  # Lista de datas que você quer selecionar
    df = df[df['Date'].isin(datas_selecionadas)]
else:
    datas_selecionadas = f'{dia}/{mes}/2024'
    df = df[df['Date'] == datas_selecionadas]

print(datas_selecionadas)
df.insert(7,'Receita Líquida', ''*df.shape[0])

if mes[0] == '0':
    mescoluna = mes[1]
else:
    mescoluna = mes
df.insert(3,'Mês', mescoluna)


df.rename(columns={'Total CPM and CPC revenue (R$)': 'Receita Bruta (R$)',
                   'Creative size': 'Tamanho do criativo',
                   'Total impressions': 'Total de impressões',
                   'Total clicks': 'Total de cliques',
                   'Total average eCPM (R$)': 'eCPM médio total (R$)',
                   'Date': 'Data',
                   'Total Active View % viewable impressions': 'Porcentagem do total de impressões visíveis do Active View',}, inplace=True)

                   
for index, row in df.iterrows(): #passa por todas linhas do dataframe e armazena o indice da coluna em 'index'
    if df.at[index, 'Advertiser'] == '-': #trocar onde o Advertiser for '-' por 'Áudio (0x0)'
        df.at[index, 'Advertiser'] = 'Áudio (0x0)'
    elif df.at[index, 'Advertiser'] == 'Total': #quando chegar na linha total, dar um break para calcular o total na mão
        break

    #substituição dos Blocos de anúncios pelo nome do portal correspondente de acordo com o dicionário em 
    #relacaoblocoportal.py
    for portal in parceiros.keys(): 
        if df.at[index, 'Ad unit'] in parceiros[portal]:
            df.at[index, 'Ad unit'] = portal
            break # Interromper o loop interno após encontrar a primeira correspondência
    if '.' in df.at[index, 'Receita Bruta (R$)']: #o arquivo xlsx coloca pontos para separar unidade de milhar das centenas, então é necessário tratá-los
        df.at[index, 'Receita Bruta (R$)'] = df.at[index, 'Receita Bruta (R$)'].replace('.','')
    df.at[index, 'Receita Bruta (R$)'] = df.at[index, 'Receita Bruta (R$)'].replace('R$','')
    
    df = calcular_receitaliq(df, 'Receita Bruta (R$)', 'Receita Líquida', index) #chama a função para o cálculo da receita líquida
    df['Receita Bruta (R$)'] = df['Receita Bruta (R$)'].replace('.',',')

df.rename(columns={'Advertiser': 'Anunciante',
                   'Ad unit': 'Bloco de anúncios'}, inplace=True)

relatorio1 = f'Acompanhamento_NE10 Edicase {dia}-{mes}.csv'
df.to_csv(f'../diarios_out/{relatorio1}', index=False)
print(relatorio1)
colunas = ["Coluna Vida Fit", "Coluna Meu Pet"]
df['Bloco de anúncios'] = df['Bloco de anúncios'].replace(colunas, 'JC Online')
colunasinterior = ["Interior - Coluna Edicase"]
df['Bloco de anúncios'] = df['Bloco de anúncios'].replace(colunasinterior, 'Interior')
relatorio2 = f'Acompanhamento_NE10 {dia}-{mes}.csv'
df.to_csv(f'../diarios_out/{relatorio2}', index=False)