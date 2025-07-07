import cloudscraper
import json
from datetime import datetime
import pandas as pd
import re
    
def get_player_birthday_country(player_name, scraper):
    """
    Obtiene la fecha de nacimiento y el país de un jugador de tenis a partir de su nombre.
    Args:
        player_name (str): Nombre del jugador de tenis.
        scraper (cloudscraper.CloudScraper): Instancia de scraper para realizar solicitudes HTTP.
    Returns:
        tuple: Fecha de nacimiento como timestamp y país del jugador.
    """
    player_name=player_name.replace(" ", "%20")
    url_player = f"https://matchstat.com/tennis/api2/profile/{player_name}?includeAll=true"
    try:
        response_player = scraper.get(url_player)

        if(response_player.status_code==200):
            json_data_player = json.loads(response_player.text)

            try:
                player_birthday = json_data_player.get('birthday')
                player_birthday_timeStamp = int(datetime.strptime(player_birthday, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
            except KeyError as e:
                print(f"Error al procesar la fecha de nacimiento: {e}")
                player_birthday_timeStamp = 0
            
            try:
                player_country = json_data_player['country']['name']
            except KeyError as e:
                print(f"Error al procesar el país: {e}")
                player_country = ""

    except Exception as e:
        print(f"Error al obtener información de {player_name}: {e}")
        player_birthday_timeStamp = 0
        player_country = ""

    return player_birthday_timeStamp, player_country

def obtener_ranking(ranking_inicial):
    """
    Obtiene el ranking de jugadores de tenis desde una API y lo organiza en un DataFrame.
    Args:
        ranking_inicial (pd.DataFrame): DataFrame con el ranking inicial de jugadores.
    Returns:
        pd.DataFrame: DataFrame con el ranking actualizado.
        bool: Indica si el ranking fue calculado o ya estaba actualizado.
    """
    if not ranking_inicial.empty:
        fechas_inicial=ranking_inicial.columns[3:].tolist()
        fechas_inicial=[datetime.fromtimestamp(int(date)).strftime('%d.%m.%Y') for date in fechas_inicial]    

    url_dates = "https://matchstat.com/tennis/api2/ranking/atp/filters?includeAll=true"

    scraper = cloudscraper.create_scraper()  # Crea un scraper que supera Cloudflare
    response = scraper.get(url_dates)

    if(response.status_code==200):
        json_data_dates=json.loads(response.text) 

        dates=json_data_dates['date']
        formatted_dates = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d.%m.%Y') for date in dates]
        #en el data set de previos, el partido más antiguo válido que tenemos es del  15 de enero de 2009
        #por lo que nos quedamos con las fechas desde esa fecha (cogemos la anterior para que ese partido entre)

        formatted_dates=[date for date in formatted_dates if datetime.strptime(date, '%d.%m.%Y')>=datetime.strptime('12.01.2009', '%d.%m.%Y')]
        dates_timestamp = [int(datetime.strptime(date, '%d.%m.%Y').timestamp()) for date in formatted_dates]
    
    if not ranking_inicial.empty:
        fechas_calcular = [date for date in formatted_dates if date not in fechas_inicial]
    else:
        fechas_calcular = formatted_dates

    if(ranking_inicial.empty):
        df_ranking = pd.DataFrame(columns=['player','birthDate','country']+list(map(int, dates_timestamp)))

    else:
        df_ranking = ranking_inicial

        fechas_calcular_timeStamp= [int(datetime.strptime(date, '%d.%m.%Y').timestamp()) for date in fechas_calcular]

        new_columns = list(map(int, fechas_calcular_timeStamp))
        df_ranking = pd.concat([df_ranking.iloc[:, :3], pd.DataFrame(columns=new_columns), df_ranking.iloc[:, 3:]], axis=1)
      
    date_to_timestamp = {formatted_dates[i]: dates_timestamp[i] for i in range(len(formatted_dates))}
    if not fechas_calcular:
        return df_ranking, False
    for date in fechas_calcular:
        print(f"Processing date: {date} de {len(fechas_calcular)}")
        timestamp = date_to_timestamp[date]
        for page in range (0, 10):
            url_page = f"https://matchstat.com/tennis/api2/ranking/atp/?date={date}&countryAcr=&group=singles&page={page}&includeAll=true"
            response_page = scraper.get(url_page)
            if(response_page.status_code==200):
                json_data_page=json.loads(response_page.text)

                for player_info in  json_data_page:
                    player_name=player_info['player']['name']
                    player_rank= player_info['position']
                    

                    if player_name in df_ranking['player'].values:
                        df_ranking.loc[df_ranking['player'] == player_name, timestamp] = player_rank
                    else:
                        # Si el jugador no está, creamos una nueva fila con NaNs y asignamos los valores de ranking
                        player_birthday_timeStamp, player_country = get_player_birthday_country(player_name, scraper)
                        nueva_fila_ranking = [player_name, player_birthday_timeStamp, player_country] + [float('nan')] * len(dates_timestamp)

                        df_ranking = pd.concat([df_ranking, pd.DataFrame([nueva_fila_ranking], columns=df_ranking.columns)], ignore_index=True)

                        # Asignamos  el ranking a la fecha correspondiente
                        df_ranking.loc[df_ranking['player'] == player_name, timestamp] = player_rank

                    
            
    df_ranking=df_ranking.fillna(-1)

    return df_ranking, True

def change_alpha3(df):
    """
    Cambia los códigos de país de los jugadores de tenis a su equivalente en formato ISO 3166-1 alpha-3.
    Args:
        df (pd.DataFrame): DataFrame que contiene la columna 'country' con los códigos de país.
    Returns:
        pd.DataFrame: DataFrame con la columna 'country' actualizada a los códigos alpha-3.
    """
    # Crear un diccionario de mapeo de códigos de países
    codigo_pais_mapping = {
        'ALG': 'DZA',  # Argelia
        'BAH': 'BHS',  # Bahamas
        'BAR': 'BRB',  # Barbados
        'BUL': 'BGR',  # Bulgaria
        'CHI': 'CHL',  # Chile
        'CRO': 'HRV',  # Croacia
        'DEN': 'DNK',  # Dinamarca
        'DOM': 'DMA',  # Dominica
        'ESA': 'SLV',  # El Salvador
        'GER': 'DEU',  # Alemania
        'GRE': 'GRC',  # Grecia
        'GUA': 'GTM',  # Guatemala
        'HAI': 'HTI',  # Haiti
        'INA': 'IDN',  # Indonesia
        'IRI': 'IRN',  # Iran
        'KUW': 'KWT',  # Kuwait
        'LAT': 'LVA',  # Letonia/Latvia
        'LIB': 'LBN',  # Líbano
        'MAS': 'MYS',  # Malasia
        'MON': 'MCO',  # Mónaco
        'NED': 'NLD',  # Países Bajos
        'PAR': 'PRY',  # Paraguay
        'PHI': 'PHL',  # Filipinas
        'POR': 'PRT',  # Portugal
        'PUR': 'PRI',  # Puerto Rico
        'RSA': 'ZAF',  # Sudáfrica
        'SLO': 'SVN',  # Eslovenia
        'SUI': 'CHE',  # Suiza
        'TOG': 'TGO',  # Togo
        'TPE': 'TWN',  # Taiwan
        'URU': 'URY',  # Uruguay
        'VIE': 'VNM',  # Vietnam
        'ZIM': 'ZWE'   # Zimbabwe
    }

    # Aplicar las conversiones
    df['country'] = df['country'].replace(codigo_pais_mapping)
    return df

def change_problematic_rows(df):
    """
    Cambia las filas problemáticas en el DataFrame de ranking de tenis.
    Args:
        df (pd.DataFrame): DataFrame que contiene la información de los jugadores.
    Returns:
        pd.DataFrame: DataFrame con las filas problemáticas corregidas."""
    #La nacionalidad de estos jugadores no es correcta, hay que cambiarla:
    df.loc[df['player'] == 'Goncalo Oliveira', 'country'] = 'VEN'
    df.loc[df['player'] == 'Marko Topo', 'country'] = 'DEU' 
    df.loc[df['player'] == 'Nicolas Moreno De Alboran', 'country'] = 'USA' 
    df.loc[df['player'] == 'Rayan Ghedjemis', 'country'] = 'DZA'
    df.loc[df['player'] == 'Tomas Lipovsek Puches', 'country'] = 'ARG' 
    df.loc[df['player'] == 'Kareem Allaf', 'country'] = 'USA' 

    #la fecha de nacimiento de roberto ortega olmedo esta mal, pone 1991-04-13 y es 1991-04-30. 
    df.loc[df['player'] == 'Roberto Ortega-Olmedo', 'birthDate'] = 672969600 
    return df

def preprocess_name(name):
    """
    Procesa el nombre de un jugador de tenis para estandarizarlo y facilitar su uso en URLs.
    Args:
        name (str): Nombre del jugador de tenis.
    Returns:
        str: Nombre procesado, estandarizado y listo para usar en URLs.
    """
    # Si hay una coma, invertir el orden del nombre y el apellido
    if ',' in name:
        parts = [part.strip() for part in name.split(',')]
        name = f"{parts[1]} {parts[0]}"  

    # Eliminar caracteres especiales
    name = re.sub(r'[^\w\s-]', '', name).strip().lower()

    parts = name.split()

    # Si hay más de 3 partes, seleccionar el primer nombre y los dos últimos apellidos
    if len(parts) > 3:
        name = f"{parts[0]} {parts[-2]} {parts[-1]}" 
    else:
        name = ' '.join(parts) 

    # Reemplazar espacios por guiones
    processed_name= name.replace(' ', '-')

    return processed_name
    
if __name__ == "__main__":
    """
    Función principal que ejecuta el programa de scraping de partidos de tenis.
    Configura los parámetros globales, descarga los partidos nuevos si es necesario, y procesa los
    partidos actuales y previos.
    """
    ruta=f'C:/INDAT/tfg_estadistica_tenis/cambio_Scraper'
    rank_inicial=False
    
    if rank_inicial:
        ranking_inicial=f'{ruta}/ranking.csv'
        ranking_inicial=pd.read_csv(ranking_inicial)
    else:
        ranking_inicial=pd.DataFrame()

        

    df_ranking, calculado =obtener_ranking(ranking_inicial)
    df_ranking = change_alpha3(df_ranking)
    df_ranking = change_problematic_rows(df_ranking)


    if calculado:
        print("Ranking actualizado")
        df_ranking.to_csv("C:/INDAT/tfg_estadistica_tenis/cambio_Scraper/ranking2.csv", index=False)
    else:
        print("Ranking ya estaba actualizado a fecha de hoy")

    
