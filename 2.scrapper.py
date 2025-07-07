import pandas as pd
import requests
import json
import re
from rapidfuzz import process, fuzz
import numpy as np
from sklearn.linear_model import LinearRegression
import sys
import os

ranking=None
players=None
ruta=None

def get_json_from_url(url, max_retries=5, timeout=30):
    """
    Obtiene un JSON de una URL con manejo de errores y reintentos.
    Args:
        url (str): URL de la que obtener el JSON.
        max_retries (int): Número máximo de reintentos en caso de error.
        timeout (int): Tiempo máximo de espera para la solicitud.
    Returns:
        dict: JSON obtenido de la URL, o None si falla.
    """
    retries = 0
    
    while retries < max_retries:
        try:
            # Realizar la solicitud
            response = requests.get(url, timeout=timeout)
            
            # Verificar el código de estado
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                if response.status_code == 404:
                    print(f"Error 404: No se encontró la URL {url}.")
                    break
                elif response.status_code==403:
                    print(f"Error 403: Acceso denegado a la URL.")
                    sys.exit(1)

                else:
                    print(f"Error {response.status_code}: {response.reason}")

        
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión: {str(e)}")
        except requests.exceptions.Timeout as e:
            print(f"Timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {str(e)}")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
        
        retries += 1
    return None

def instanciar_variables_globales(nuevo):
    """
    Inicializa las variables globales y carga los datos de los archivos CSV si existen.
    Args:
        nuevo (bool): Si es True, se crea un nuevo DataFrame para players, si es False, se carga desde el archivo CSV.
    """
    global players, ranking, ruta
    if not nuevo:
        archivo_players = f'{ruta}/players.csv'
        if os.path.exists(archivo_players):
            players = pd.read_csv(archivo_players)
    elif nuevo or not os.path.exists(archivo_players):
        players = pd.DataFrame(columns=[
            'id','birthDate', 'height', 'weight', 'rightHanded', 'fullName', 'country'
        ])

    archivo_ranking = f'{ruta}/ranking/ranking.csv'
    if os.path.exists(archivo_ranking):
        ranking = pd.read_csv(archivo_ranking)
        ranking['player'] = [preprocess_name(name) for name in ranking['player']]
    else:
        print(f"El archivo {archivo_ranking} no existe. Asegúrate de que el archivo esté en la ruta correcta.")
        sys.exit(1)
        
def safe_divide(numerator, denominator, precision=4):
    """Realiza una división segura, evitando la división por cero.
    Args:
        numerator (float): Numerador de la división.
        denominator (float): Denominador de la división.
        precision (int): Número de decimales a redondear.
    Returns:
        float: Resultado de la división redondeado a la precisión especificada, o None si el denominador es cero.
    """
    if denominator == 0:
        return 
    return round(numerator / denominator, precision)

def preprocess_name(name):
    """Preprocesa un nombre para estandarizarlo y facilitar su comparación.
    Args:
        name (str): Nombre a preprocesar.
    Returns:
        str: Nombre preprocesado, con espacios reemplazados por guiones y en minúsculas.
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
    return name.replace(' ', '-')

def fraccion_a_decimal(fraccion):
    """
    Convierte una fracción o un número en formato de cadena a su valor decimal.
    Args:
        fraccion (str): Fracción en formato de cadena o número.
    Returns:
        float: Valor decimal de la fracción, o None si no se puede convertir.
    """
    if fraccion is None or pd.isna(fraccion) or fraccion == '':
        return None
    try:
        if '/' in str(fraccion):
            numerador, denominador = map(float, str(fraccion).split('/'))
            return numerador / denominador
        else:
            return float(fraccion)
    except (ValueError, ZeroDivisionError):
        return None
    
def scraping_tournaments():
    """
    Scrapea los torneos de tenis de la API de SofaScore.
    Returns:
        list: Lista de IDs de torneos válidos.
    """
    id_tournaments = []
    url_tournaments= "https://www.sofascore.com/api/v1/category/3/unique-tournaments"
   
    json_data_tournaments = get_json_from_url(url_tournaments)
    id_tournaments = []
    for month in json_data_tournaments['groups']:
        for tournament in month['uniqueTournaments']:    
            try:
                if tournament['tennisPoints'] in [500,1000,2000] and 'Doubles' not in tournament['name'] and 'Double'  not in tournament['name']:
                    id_tournaments.append(tournament['id'])
            except KeyError:
                pass
            
            if tournament['name'] == 'ATP Finals':
                id_tournaments.append(tournament['id'])
    
    id_tournaments = list(set(id_tournaments))
    return id_tournaments

def scraping_seasons(id_tournaments, year):
    """Scrapea las temporadas de los torneos de tenis para un año específico.
    Args:
        id_tournaments (list): Lista de IDs de torneos.
        year (int): Año para el que se quieren las temporadas.
    Returns:
        list: Lista de tuplas con el ID del torneo y el ID de la temporada.
    """
    filtered_tournaments = id_tournaments.copy()
    if (year==2024):
        if 2400 in filtered_tournaments:
            filtered_tournaments.remove(2420) #Doha
        if 18377 in filtered_tournaments:
            filtered_tournaments.remove(18377) #Dallas
        if 2390 not in filtered_tournaments:
            filtered_tournaments.append(2390) #Montreal
        if 2491 in filtered_tournaments:
            filtered_tournaments.remove(2491) #munich
    elif (year==2023):
        if 2400 in filtered_tournaments:
            filtered_tournaments.remove(2420) #Doha
        if 18377 in filtered_tournaments:
            filtered_tournaments.remove(18377) #Dallas
        if 2491 in filtered_tournaments:
            filtered_tournaments.remove(2491) #munich
        if 2510 not in filtered_tournaments:
            filtered_tournaments.append(2510) #toronto
    elif (year==2022):
        if 2400 in filtered_tournaments:
            filtered_tournaments.remove(2420) #Doha
        if 18377 in filtered_tournaments:
            filtered_tournaments.remove(18377) #Dallas
        if 2390 not in filtered_tournaments:
            filtered_tournaments.append(2390) #Montreal
        if 2491 in filtered_tournaments:
            filtered_tournaments.remove(2491) #munich
        if 15952 not in filtered_tournaments:
            filtered_tournaments.append(15952) #astana

    elif (year==2021):
        if 2400 in filtered_tournaments:
            filtered_tournaments.remove(2420) #Doha
        if 2491 in filtered_tournaments:
            filtered_tournaments.remove(2491) #munich
        if 2510 not in filtered_tournaments:
            filtered_tournaments.append(2510) #toronto
    
    id_tournaments_seasons = []
    for id in filtered_tournaments:
        url_seasons = f"https://www.sofascore.com/api/v1/unique-tournament/{id}/seasons"
        json_data_seasons = get_json_from_url(url_seasons)
        for season in json_data_seasons['seasons']:
            if(int(season['year']) == year):
                id_tournaments_seasons.append((id, season['id']))
                print(season['name'])
 
    return id_tournaments_seasons

def scraping_id_matches(id_tournaments_seasons):
    """Scrapea los IDs de los partidos de tenis de los torneos y temporadas especificados.
    Args:
        id_tournaments_seasons (list): Lista de tuplas con el ID del torneo y el ID de la temporada.
    Returns:
        list: Lista de IDs de partidos.
    """
    id_partidos = []
    for tournament,season in id_tournaments_seasons:
        print(tournament, season)
        for i in range (10, -1, -1):
            url_tournament_season=f"https://www.sofascore.com/api/v1/unique-tournament/{tournament}/season/{season}/events/last/"+str(i)
            json_data_tournament_season = get_json_from_url(url_tournament_season)
            if json_data_tournament_season is None:
                continue
            else:
                for j in range (len(json_data_tournament_season['events'])):
                    id_partidos.append(json_data_tournament_season['events'][j]['id'])
    
    return id_partidos

def scraping_partido(id_partido, actual):
    """
    Scrapea los datos de un partido de tenis específico.
    Args:
        id_partido (int or dict): ID del partido o un diccionario con los datos del partido.
        actual (bool): Si es True, se obtienen las probabilidades actuales, si es False, se obtienen los resultados previos.
    Returns:
        pd.DataFrame: DataFrame con los datos del partido.
    """
    df = pd.DataFrame(columns=[
            #Identificadores de partido
            'idTournament', 'tournamentName','idSeason', 'idEvent', 'round','groundType','periodCount',

            #Target
            'winnerCode',

            #------------------------------------Caracterísitcas a priori----------------------------------------------#
            #Datos temporales del partido
            'startTimestamp','year',

            #Datos del jugador local
            'idHome', 'birthDateHome','ActualRankingHome', 'BestRankingHome', 'BestRankingDateHome', 
            'HeightHome', 'WeightHome', 'RightHandedHome', 'countryHome',

            #Datos del jugador visitante
            'idAway', 'birthDateAway','ActualRankingAway', 'BestRankingAway', 'BestRankingDateAway',
            'HeightAway', 'WeightAway', 'RightHandedAway',  'countryAway',

            #----------------------------Características a posteriori:-------------------------------------------------------#
            #Estado del partido
            'status', 
    
    ])
    if actual:
        columnas_actual=[
            'ProbabilityHome', 'ProbabilityAway'
        ]
        df=pd.DataFrame(columns=df.columns.tolist() + columnas_actual)
    else:
        columnas_previos=[
        #Datos de resultado del partido
        'homeScore', 'awayScore',

        # Datos de resultados en los sets: -1 si no existen
        'set1performanceHome', 'set1performanceAway',
        'set2performanceHome', 'set2performanceAway',
        'set3performanceHome', 'set3performanceAway',
        'set4performanceHome', 'set4performanceAway',
        'set5performanceHome', 'set5performanceAway',

        # Datos de juegos totales
        'totalGamesHome', 'totalGamesAway'
        ]
        df=pd.DataFrame(columns=df.columns.tolist() + columnas_previos)
    

    #Identificadores de partido
    if(actual):
        df.loc[0,'idEvent']=int(id_partido)
        url_match="https://www.sofascore.com/api/v1/event/"+str(int(df.loc[0,'idEvent']))
        json_data = get_json_from_url(url_match)['event']
    else:
        json_data = id_partido
        df.loc[0,'idEvent']=int(json_data['id'])
    
    try:
        df.loc[0,'idTournament']=json_data['tournament']['uniqueTournament']['id']
    except KeyError:
        df.loc[0,'idTournament']=None
    try:
        df.loc[0,'tournamentName']=json_data['tournament']['uniqueTournament']['name']
    except KeyError:
        df.loc[0,'tournamentName']=None
    try:
        df.loc[0,'idSeason']=json_data['season']['id']
    except KeyError:
        df.loc[0,'idSeason']=None
    try:
        df.loc[0,'groundType']=json_data['groundType']
    except KeyError:   
        df.loc[0,'groundType']=None
    try:
        df.loc[0,'round']=json_data['roundInfo']['round']
    except KeyError:
        df.loc[0,'round']=None

    #Solo es al mejor de 5 grand Slam , por lo que si no se encuentra periodCount, será un partido de cateogría inferior caso especial en estos torneos
    try:
        if(df.loc['tournamentName'].isin(['Next Gen Finals', 'Australian Open Australian Playoff'])):
            df.loc[0,'periodCount']=5
        else:
            df.loc[0,'periodCount']=json_data['defaultPeriodCount']
    except KeyError:
        df.loc[0,'periodCount']=3
    

    #fecha y año del partido
    try:
        df.loc[0,'startTimestamp']=json_data['startTimestamp']
    except KeyError:
        df.loc[0,'startTimestamp']=None

    try:
        df.loc[0,'year']=json_data['season']['year']
    except KeyError:   
        df.loc[0,'year']=None
    
    
    tour=df.loc[0, 'tournamentName']
    if tour is not None:
        if any(substring in df.loc[0,'tournamentName'] for substring in ['Exhibition','Davis','Doubles','Double']):
            #print('Torneo no válido: ', df.loc[0,'tournamentName'])
            df.loc[0,'idHome']=None
            df.loc[0,'idAway']=None
            return df
    
    #Identificadores del jugador home
    id_home=json_data['homeTeam']['id']
    homePlayer= get_player(id_home, df.loc[0,'startTimestamp'])
    df.loc[0,'idHome']=homePlayer['id'].values[0]
    df.loc[0,'birthDateHome']=homePlayer['birthDate'].values[0]
    df.loc[0,'HeightHome']=homePlayer['height'].values[0]
    df.loc[0,'WeightHome']=homePlayer['weight'].values[0]
    df.loc[0,'RightHandedHome']=homePlayer['rightHanded'].values[0]
    df.loc[0,'countryHome']=homePlayer['country'].values[0]
    df.loc[0,'ActualRankingHome']=homePlayer['actualRanking'].values[0]
    df.loc[0,'BestRankingHome']=homePlayer['bestRanking'].values[0]
    df.loc[0,'BestRankingDateHome']=homePlayer['bestRankingDate'].values[0]

    id_away=json_data['awayTeam']['id']
    awayPlayer=get_player(id_away,df.loc[0,'startTimestamp'])
    df.loc[0,'idAway']=awayPlayer['id'].values[0]
    df.loc[0,'birthDateAway']=awayPlayer['birthDate'].values[0]
    df.loc[0,'HeightAway']=awayPlayer['height'].values[0]
    df.loc[0,'WeightAway']=awayPlayer['weight'].values[0]
    df.loc[0,'RightHandedAway']=awayPlayer['rightHanded'].values[0]
    df.loc[0,'countryAway']=awayPlayer['country'].values[0]
    df.loc[0,'ActualRankingAway']=awayPlayer['actualRanking'].values[0]
    df.loc[0,'BestRankingAway']=awayPlayer['bestRanking'].values[0]
    df.loc[0,'BestRankingDateAway']=awayPlayer['bestRankingDate'].values[0]

    #----------------------------------- Target---------------------------------------------------------------#
    try:
        df.loc[0,'winnerCode']=json_data['winnerCode']-1
    except:
        df.loc[0,'winnerCode']=None
    #----------------------------------- Probabilidades de victoria ------------------------------------------#
    if actual:
        # Extraer las probabilidades de victoria
        probabilidades = extraer_odds(df.loc[0,'idEvent'])
        if probabilidades is not None:
            df.loc[0, 'ProbabilityHome'] = probabilidades[0]
            df.loc[0, 'ProbabilityAway'] = probabilidades[1]
        else:
            df.loc[0, 'ProbabilityHome'] = None
            df.loc[0, 'ProbabilityAway'] = None

    #----------------------------------- Características a posteriori-----------------------------------------#
    #Estado del partido
    try:
        df.loc[0,'status']=json_data['status']['code']
    except KeyError:
        df.loc[0,'status']=None

    if not(actual):
        #Datos de resultado del partido
        try:
            df.loc[0,'homeScore']=json_data['homeScore']['current']
        except KeyError:
            df.loc[0,'homeScore']=None
        try:
            df.loc[0,'awayScore']=json_data['awayScore']['current']
        except KeyError:
            df.loc[0,'awayScore']=None

        # Datos de resultados en los sets: -1 si no existen
        for set_num in range(1, 6):  # Para sets del 1 al 5
            for team, team_key in [('Home', 'homeScore'), ('Away', 'awayScore')]:
                column_name = f'set{set_num}performance{team}'
                period_key = f'period{set_num}'
                
                try:
                    df.loc[0, column_name] = json_data[team_key][period_key]
                except KeyError:
                    df.loc[0, column_name] = 0

        df.loc[0, 'totalGamesHome'] = sum(val for val in [
                df.loc[0, 'set1performanceHome'],
                df.loc[0, 'set2performanceHome'],
                df.loc[0, 'set3performanceHome'],
                df.loc[0, 'set4performanceHome'],
                df.loc[0, 'set5performanceHome']
            ] if val != -1)
            
        df.loc[0, 'totalGamesAway'] = sum(val for val in [
                df.loc[0, 'set1performanceAway'],
                df.loc[0, 'set2performanceAway'],
                df.loc[0, 'set3performanceAway'],
                df.loc[0, 'set4performanceAway'],
                df.loc[0, 'set5performanceAway']
            ] if val != -1)
    return df

def extraer_odds(id_match):
    """
    Extrae las probabilidades de victoria de un partido de tenis a partir de su ID.
    Args:
        id_match (int): ID del partido.
    Returns:
        tuple: Probabilidades de victoria del jugador local y visitante, o (None, None) si no se pueden obtener.
    """
    url_odds = f'https://www.sofascore.com/api/v1/event/{id_match}/odds/1/featured'
    json_data_odds = get_json_from_url(url_odds)
    if json_data_odds is None:
        print("No se pudieron obtener datos de odds")
        return (None, None)
    else:
        try:
            json_data_odds_featured = json_data_odds['featured']['default']['choices']
            initialFractionalValueHome = json_data_odds_featured[0]['initialFractionalValue']
            initialFractionalValueAway = json_data_odds_featured[1]['initialFractionalValue']
            
            # Convertir valores fraccionales a decimales
            initialDecimalValueHome = fraccion_a_decimal(initialFractionalValueHome)
            initialDecimalValueAway = fraccion_a_decimal(initialFractionalValueAway)
            
            # Verificar que los valores decimales no sean None antes de calcular
            if initialDecimalValueHome is not None and initialDecimalValueAway is not None:
                # Las cuotas decimales incluyen la devolución de la apuesta
                initialOddsHome = initialDecimalValueHome + 1
                initialOddsAway = initialDecimalValueAway + 1
                
                # Calcular probabilidades implícitas
                probabilityHome = 1 / initialOddsHome if initialOddsHome != 0 else None
                probabilityAway = 1 / initialOddsAway if initialOddsAway != 0 else None
                
                return (probabilityHome, probabilityAway)
            else:
                print(f"No se pudieron convertir los valores fraccionales: Home={initialFractionalValueHome}, Away={initialFractionalValueAway}")
                return (None, None)
        
        except (KeyError, IndexError) as e:
            print(f"Error al extraer odds: {e}")
            return (None, None)
        
def get_player(id, startTimeStamp):
    """
    Obtiene los datos de un jugador de tenis a partir de su ID y la fecha de inicio del partido.
    Args:
        id (int): ID del jugador.
        startTimeStamp (int): Marca de tiempo de inicio del partido.
    Returns:
        pd.DataFrame: DataFrame con los datos del jugador, incluyendo ID, fecha de nacimiento, altura, peso, mano dominante, país, ranking actual y mejor ranking.
    """
    global ranking, players, ruta
    df_return = pd.DataFrame(columns=[
            'id','birthDate', 'height', 'weight', 'rightHanded', 'country', 'actualRanking', 'bestRanking', 'bestRankingDate'
    ])
    df_return.loc[0,'id']=id
    player = players.loc[players['id'] == id]
    
    if player.empty:
        player = scraping_individual_player(id)
        
        # Verificar si player está vacío antes de intentar acceder a sus valores
        if player.empty or ( '/' in player['fullName'].values[0]):
            # Rellenar df_return con valores predeterminados o nulos
            df_return['birthDate'] = None
            df_return['height'] = None
            df_return['weight'] = None
            df_return['rightHanded'] = None
            df_return['country'] = None
            df_return['actualRanking'] = -100
            df_return['bestRanking'] = -100
            df_return['bestRankingDate'] = None
            return df_return
            
        else:
            players = pd.concat([players, player], ignore_index=True)

    if not player.empty:
        name_player = player['fullName'].values[0]
        df_return.loc[0,'birthDate']=player['birthDate'].values[0]
        df_return.loc[0,'height']=player['height'].values[0]
        df_return.loc[0,'weight']=player['weight'].values[0]
        df_return.loc[0,'rightHanded']=player['rightHanded'].values[0]
        df_return.loc[0,'country']=player['country'].values[0]
        #Ranking del jugador en el momento del partido
        columnas_ranking=[int(col) for col in ranking.columns[3:]]
        relevant_dates = [col for col in columnas_ranking if col <= startTimeStamp]

        if not relevant_dates:
            df_return.loc[0,'ActualRanking']=-100
            df_return.loc[0,'BestRanking']=-100

        else:
            try:
                if not pd.isnull(df_return.loc[0,'birthDate']):
                    name_player_preprocessed=preprocess_name(name_player)

                    if name_player_preprocessed in ranking['player'].values:
                        matched_player=name_player_preprocessed
                    else:  
                        #filtramos los jugadores por la fecha de nacimiento en +/- 5 días
                        closest_matches_country = ranking[ranking['country'] == df_return.loc[0,'country']]
                        closest_matches_to_birtday = ranking[ranking['birthDate'].isin(range(int(df_return.loc[0, 'birthDate'])-259200, int(df_return.loc[0, 'birthDate'])+259200))]

                        closest_matches = pd.merge(closest_matches_country, closest_matches_to_birtday, on='player', how='inner')

                        if(closest_matches.empty):
                            matched_player=None
                            print(f"No hay un match válido para {name_player_preprocessed} porque no hay coincidencia de cumpleaños (no existe, ej jugador joven).")
                        else:
                            best_match, score , _= process.extractOne(
                                name_player_preprocessed, closest_matches['player'].values, scorer=fuzz.token_sort_ratio
                            )
                            
                            if score>= 45:
                                matched_player=best_match
                                ranking.loc[ranking['player'] == matched_player, 'player'] = name_player_preprocessed
                                print("matched", matched_player, "player", name_player_preprocessed, "score", score)
                                
                                with open(f'{ruta}/matches.txt', 'a' , encoding='utf-8') as archivo:
                                    archivo.write(f'matched {matched_player} player {name_player_preprocessed} score {score} \n')  
                                    
                            else:
                                matched_player=None
                                print(f"No hay un match válido para {name_player_preprocessed} con score {score}. El mejor match ({best_match}) fue descartado.")
                        
                        

                    if(matched_player):   
                        closest_date = max(relevant_dates)
                        ranking_fecha = ranking[['player', str(closest_date)]].copy()
                        ranking_fecha.columns = ['player', 'Ranking']
                        
                        ranking_fecha_player=ranking_fecha[ranking_fecha['player'] == name_player_preprocessed]['Ranking'].values[0]
                        if(ranking_fecha_player == -1):
                            df_return.loc[0,'actualRanking']=-100
                        else:
                            df_return.loc[0,'actualRanking'] = 901-ranking_fecha_player


                        fila_jugador = ranking.loc[ranking['player'] == name_player_preprocessed].drop(columns=['player','birthDate', 'country'])
                        rankings_date = fila_jugador.loc[:, fila_jugador.columns.astype(int) <= closest_date]
                        if(((rankings_date).values!= -1).any()):
                            mejor_ranking=rankings_date[rankings_date!=-1].min(axis=1).values[0]
                            columna_min=rankings_date[rankings_date!=-1].idxmin(axis=1).values[0]
                            df_return.loc[0,'bestRanking'] = 901-mejor_ranking
                            df_return.loc[0,'bestRankingDate'] = columna_min
                            
                        else:
                            df_return.loc[0,'bestRanking']=-100
                        
                        #print("best ranking", df.loc[0,'aestRanking'])            
                        
                    else:
                        df_return.loc[0,'actualRanking']=-100
                        df_return.loc[0,'bestRanking']=-100
                
            except KeyError:
                df_return.loc[0,'id']=None
    else:
        # El jugador no estaba en la base local y no se pudo obtener, rellenar con valores predeterminados
        df_return['birthDate'] = None
        df_return['height'] = None
        df_return['weight'] = None
        df_return['rightHanded'] = None
        df_return['country'] = None
        df_return['actualRanking'] = -100
        df_return['bestRanking'] = -100
        df_return['bestRankingDate'] = None

    return df_return

def scraping_individual_player(id):
    """
    Scrapea los datos de un jugador de tenis individual a partir de su ID.
    Args:
        id (int): ID del jugador.
    Returns:
        pd.DataFrame: DataFrame con los datos del jugador, incluyendo ID, fecha de nacimiento, altura, peso, mano dominante, país y ranking.
    """
    urlJugador="https://www.sofascore.com/api/v1/team/"+str(id)
    json_data2= get_json_from_url(urlJugador)
    df_player=pd.DataFrame(columns=[
            'id','birthDate', 'height', 'weight', 'rightHanded', 'fullName', 'country'
    ])
    df_player.loc[0,'id']=id
    try:
        fechaTimeStamp=json_data2['team']['playerTeamInfo']['birthDateTimestamp']
        df_player.loc[0, 'birthDate'] = fechaTimeStamp
    except KeyError:
        df_player.loc[0, 'birthDate'] = None
    
    try:
        df_player.loc[0,'fullName']=json_data2['team']['fullName']
    except KeyError:
        df_player.loc[0,'fullName']=None

    try:
        df_player.loc[0,'weight']=json_data2['team']['playerTeamInfo']['weight']
    except KeyError:
        df_player.loc[0,'weight']=None

    try:
        if json_data2['team']['playerTeamInfo']['plays']=='right-handed':
            df_player.loc[0,'rightHanded']=1
        else:
            df_player.loc[0,'rightHanded']=0
    except KeyError:
        df_player.loc[0,'rightHanded']=None

    try:
        df_player.loc[0,'height']=json_data2['team']['playerTeamInfo']['height']
    except KeyError:
        df_player.loc[0,'height']=None
    
    try:
        df_player.loc[0,'country']=json_data2['team']['country']['alpha3']
    except KeyError:
        df_player.loc[0,'country']=None
    
    return df_player

def get_last_matches(id_player, id_event,num_previos):
    """
    Obtiene los últimos partidos de un jugador de tenis a partir de su ID y el ID del partido actual.
    Args:
        id_player (int): ID del jugador.
        id_event (int): ID del partido actual.
        num_previos (int): Número de partidos anteriores a obtener.
    Returns:
        pd.DataFrame: DataFrame con los datos de los últimos partidos del jugador.
    """
    df_return = pd.DataFrame() 
    partido_actual=id_event 
    found_current_match=False
    page=0
    while(df_return.shape[0]<num_previos):
        try:
            url_last_matches_player=f"https://www.sofascore.com/api/v1/team/{id_player}/events/last/{page}"
            print(url_last_matches_player)
            json_data_last_player = get_json_from_url(url_last_matches_player)['events']
            events=list(reversed(json_data_last_player))
            for j,event in enumerate(events):
                if(df_return.shape[0]>=num_previos):
                    break

                current_id=event['id']

                if(current_id==id_event):
                    found_current_match=True
                    continue

                if(found_current_match):
                    last_match_timestamp = None
                    # Verificar si hay un partido anterior en esta página

                    if j+1 < len(events):
                        original_index = len(json_data_last_player) - 1 - (j+1)
                        last_match_timestamp = json_data_last_player[original_index]['startTimestamp']
                        
                    # Si no hay partido anterior en esta página, buscar en la página siguiente
                    if last_match_timestamp is None:
                        try:
                            next_page_url = f"https://www.sofascore.com/api/v1/team/{id_player}/events/last/{page+1}"
                            next_page_data = get_json_from_url(next_page_url)['events']    
                            if len(next_page_data) > 0:
                                # El último evento de la página anterior
                                last_event = next_page_data[len(next_page_data)-1]  # Tomamos el primer evento (más reciente)
                                last_match_timestamp = last_event['startTimestamp']
 
                        except:
                            continue
                    
                    df_partido_individual = scraping_partido(event, False)
                    df_partido_individual['lastMatchTimestamp'] = last_match_timestamp
                    df_partido_individual['idNext']=partido_actual

                    no_data = filtrar_partido(df_partido_individual, False)
 
                    if no_data:
                        continue

                    partido_actual=current_id

                    df_return=pd.concat([df_return, df_partido_individual],ignore_index=True)
            page+=1

        except (Exception, KeyError) as e:
            print(f"Error al obtener página {page} de partidos:")
            break

    return df_return
    
def filtrar_partido(df_partido, actual):
    """
    Filtra un partido de tenis según una serie de condiciones para determinar si debe ser seleccionado.
    Args:
        df_partido (pd.DataFrame): DataFrame con los datos del partido.
        actual (bool): Si es True, se filtran partidos actuales, si es False, se filtran partidos previos.
    Returns:
        bool: True si el partido no cumple las condiciones de selección, False si sí las cumple
    """
    #si el partido está vacío, no se selecciona (no debería pasar)
    if df_partido.empty:
        #print('Partido vacío')
        return True
    if df_partido.loc[0,'idHome'] is None or df_partido.loc[0,'idAway'] is None:
        #print('Partido sin jugadores')
        return True
    if pd.isna(df_partido.loc[0,'tournamentName']):
        #print('Torneo vacío')
        return True
    
    #nombres de los torneos, elimino exhibiciones, copa davis y dobles
    if any(substring in df_partido.loc[0,'tournamentName'] for substring in ['Exhibition','Davis','Doubles','Double']):
        #print(f"Torneo no válido: {df_partido_actual.loc[0,'tournamentName']}")
        return True
    
    #si no hay tipo de suelo, no se selecciona
    if pd.isna(df_partido.loc[0,'groundType']):
        #print('Tipo de suelo vacío')
        return True
    
    #si no hay ganador, no se selecciona
    if pd.isna(df_partido.loc[0,'winnerCode']):
        #print('Ganador vacío')
        return True

    #si el partido está cancelado o retirada antes de jugar, no se selecciona o si está descalificado o pospuesto, SOLO PARTIDOS TERMINADOS
    #if df_partido.loc[0,'status'] in [92, 70,91,97,98, 60]:
    if df_partido.loc[0,'status'] != 100:
        #print('Partido cancelado o retirada antes de jugar')
        return True
    
    #print(df_partido_actual.columns)
    #si no tengo altura y peso, no selecciono (una de las dos sí porque puedo imputar por regresion)
    #print(df_partido_actual.loc[0,'WeightHome'],df_partido_actual.loc[0,'HeightHome'])
    if pd.isna(df_partido.loc[0,'WeightHome']) and pd.isna(df_partido.loc[0, 'HeightHome']):
        #print('home vacío')
        return True
    if pd.isna(df_partido.loc[0,'WeightAway']) and pd.isna(df_partido.loc[0, 'HeightAway']):
        #print('away vacío')
        return True
    
    #si no tengo datos del jugador (todo incompleto excepto el id), no selecciono,
    # se toma de referencia el cumpleaños
    #print(df_partido_actual.loc[0,'birthDateHome'],df_partido_actual.loc[0,'birthDateAway'])
    if pd.isna(df_partido.loc[0,'birthDateHome']) or pd.isna(df_partido.loc[0,'birthDateAway']):
        #print('Datos del jugador vacíos')
        return True

    #Si el partido que hay que filtrar es un actual, no puede ser -100 ningun ranking
    if (actual):
        if df_partido.loc[0,'ActualRankingHome'] == -100 and df_partido.loc[0,'BestRankingHome'] == -100:
            #print('Ranking actual vacío')
            return True
        if df_partido.loc[0,'ActualRankingAway'] == -100 and df_partido.loc[0,'BestRankingAway'] == -100:
            #print('Ranking actual vacío')
            return True
    
    if not(actual):
        #si no hay resultado de cada jugador, no se selecciona
        if pd.isna(df_partido.loc[0,'homeScore']) or pd.isna(df_partido.loc[0,'awayScore']):
            #print('Resultado vacío')
            return True
        #si el resultado es 0-0 no se selecciona
        if (df_partido.loc[0,'homeScore']==0) and (df_partido.loc[0,'awayScore']==0):
            #print('Resultado 0-0')
            return True
    
    return False

def impute_player_data(previos):
    """
    Imputa los datos de altura y peso de los jugadores en el DataFrame previos. Utiliza regresión lineal para predecir los valores faltantes basándose en los
    valores de los jugadores que tienen ambos datos disponibles.
    Args:
        previos (pd.DataFrame): DataFrame con los datos de los partidos previos.
    Returns:
        pd.DataFrame: DataFrame con los datos imputados.
    """
    # Crear una copia del DataFrame completo
    print('Imputando datos')
    result = previos.copy()
    
    # Identificar filas con NA en altura y peso
    player_columns = ['HeightHome', 'WeightHome', 'HeightAway', 'WeightAway', 'RightHandedHome', 'RightHandedAway']
    rows_with_na = previos[previos[player_columns].isna().any(axis=1)]
    
    if len(rows_with_na) == 0:
        return result  # No hay nada que imputar
    
    # 1. RightHanded a 1
    result['RightHandedHome'] = result['RightHandedHome'].fillna(1)
    result['RightHandedAway'] = result['RightHandedAway'].fillna(1)
    
    # 2. Preparar datos combinados para la regresión
    # Concatenar datos de Home y Away
    heights = pd.concat([result['HeightHome'], result['HeightAway']])
    weights = pd.concat([result['WeightHome'], result['WeightAway']])
    
    # Datos disponibles para regresión
    mask_complete = (~heights.isna()) & (~weights.isna())
    # Para identificar filas donde ambos valores (altura y peso) son NaN para un mismo jugador
    # Jugadores locales con ambos valores NaN

    if mask_complete.any():
        reg = LinearRegression()
        
        # Si hay alturas que faltan, predecir con peso
        if heights.isna().any():
            # Entrenar con datos completos
            X = weights[mask_complete].values.reshape(-1, 1)
            y = heights[mask_complete].values
            reg.fit(X, y)
            
            # Predecir alturas faltantes
            if result['HeightHome'].isna().any():
                mask_height_na = result['HeightHome'].isna()
                X_pred = result.loc[mask_height_na, 'WeightHome'].values.reshape(-1, 1)
                result.loc[mask_height_na, 'HeightHome'] = reg.predict(X_pred)
            
            if result['HeightAway'].isna().any():
                mask_height_na = result['HeightAway'].isna()
                X_pred = result.loc[mask_height_na, 'WeightAway'].values.reshape(-1, 1)
                result.loc[mask_height_na, 'HeightAway'] = reg.predict(X_pred)
        
        # Si hay pesos que faltan, predecir con altura
        if weights.isna().any():
            # Entrenar con datos completos
            X = heights[mask_complete].values.reshape(-1, 1)
            y = weights[mask_complete].values
            reg.fit(X, y)
            
            # Predecir pesos faltantes
            if result['WeightHome'].isna().any():
                mask_weight_na = result['WeightHome'].isna()
                X_pred = result.loc[mask_weight_na, 'HeightHome'].values.reshape(-1, 1)
                result.loc[mask_weight_na, 'WeightHome'] = reg.predict(X_pred)
            
            if result['WeightAway'].isna().any():
                mask_weight_na = result['WeightAway'].isna()
                X_pred = result.loc[mask_weight_na, 'HeightAway'].values.reshape(-1, 1)
                result.loc[mask_weight_na, 'WeightAway'] = reg.predict(X_pred)
    
    return result

def reorganizar_partidos(actual,previos,num_previos=50):
    """
    Reorganiza los partidos previos para que coincidan con el formato (home/away) de los partidos actuales.
    Args:
        actual (pd.DataFrame): DataFrame con los partidos actuales.
        previos (pd.DataFrame): DataFrame con los partidos previos.
        num_previos (int): Número de partidos previos a considerar para cada partido actual.
    Returns:
        pd.DataFrame: DataFrame con los partidos previos reorganizados.
    """
    df_previos_reorganizado=previos.copy()
    for idx in range(actual.shape[0]):
        partido_actual=actual.iloc[idx,:]
        id_home_actual=partido_actual['idHome']
        id_away_actual=partido_actual['idAway']
        
        print(f"Procesando partido actual {idx}, Home ID: {id_home_actual}, Away ID: {id_away_actual}")

        inicio_home= idx*num_previos*2
        fin_home=inicio_home+num_previos-1
        inicio_away=fin_home+1
        fin_away=inicio_away+num_previos-1

        for i in range(inicio_home,fin_home+1):
            if(previos.loc[i,'idAway'] == id_home_actual):
                df_previos_reorganizado.loc[i] = intercambiar_home_away(previos.loc[i])
                if i < len(previos) and df_previos_reorganizado.loc[i, 'idHome'] != id_home_actual:
                    print(f"Error: En el índice {i}, después de la reorganización idHome = {df_previos_reorganizado.loc[i, 'idHome']}, esperado {id_home_actual}")

        for i in range(inicio_away,fin_away+1):
            if(previos.loc[i,'idHome'] == id_away_actual):
                df_previos_reorganizado.loc[i] = intercambiar_home_away(previos.loc[i])
                if i < len(previos) and df_previos_reorganizado.loc[i, 'idAway'] != id_away_actual:
                    print(f"Error: En el índice {i}, después de la reorganización idAway = {df_previos_reorganizado.loc[i, 'idAway']}, esperado {id_away_actual}")

    return df_previos_reorganizado

def intercambiar_home_away(partido):
    """
    Intercambia las columnas Home y Away de un partido de tenis, incluyendo los IDs de los jugadores.
    Args:
        partido (pd.Series): Serie con los datos del partido.
    Returns:   
        pd.Series: Serie con las columnas Home y Away intercambiadas.
    """
    partido_reorganizado=partido.copy()

    columnas=partido.index.tolist()
    columnas_home = [col for col in columnas if 'Home' in col]
    columnas_away = [col for col in columnas if 'Away' in col]
    
    # Intercambiar valores entre columnas Home y Away
    for col_home in columnas_home:
        col_away = col_home.replace('Home', 'Away')
        if col_away in columnas_away:
            # Almacenar temporalmente los valores para intercambiarlos correctamente
            temp_home = partido[col_home]
            temp_away = partido[col_away]
            partido_reorganizado[col_home] = temp_away
            partido_reorganizado[col_away] = temp_home
    
    # Intercambiar explícitamente idHome e idAway
    temp_id_home = partido['idHome']
    temp_id_away = partido['idAway']
    partido_reorganizado['idHome'] = temp_id_away
    partido_reorganizado['idAway'] = temp_id_home
    
    #partido_reorganizado['idHome'], partido_reorganizado['idAway'] = partido_reorganizado['idAway'], partido_reorganizado['idHome']

    #ajuste del ganador
    if partido_reorganizado['winnerCode']==0:
        partido_reorganizado['winnerCode']=1
    elif partido_reorganizado['winnerCode']==1:
        partido_reorganizado['winnerCode']=0

    return partido_reorganizado

def invertir_bloques(df, tamano_bloque=50):
    """    Invierte los bloques de un DataFrame en bloques de tamaño fijo.
    Args:
        df (pd.DataFrame): DataFrame a invertir.
        tamano_bloque (int): Tamaño de los bloques a invertir.
    Returns:
        pd.DataFrame: DataFrame con los bloques invertidos.
    """
    # Creamos un DataFrame vacío para almacenar el resultado
    df_invertido = pd.DataFrame(columns=df.columns)
    
    # Calculamos el número de bloques completos
    num_filas = len(df)
    num_bloques = num_filas // tamano_bloque
    
    # Procesamos cada bloque
    for i in range(0, num_bloques):
        print(f"Procesando bloque {i} de {num_bloques}")
        # Índices de inicio y fin del bloque actual
        inicio = i * tamano_bloque
        fin = inicio + tamano_bloque
        
        # Extraemos el bloque y lo invertimos
        bloque = df.iloc[inicio:fin].copy()
        bloque_invertido = bloque.iloc[::-1].reset_index(drop=True)
        
        # Añadimos el bloque invertido al nuevo DataFrame
        df_invertido = pd.concat([df_invertido, bloque_invertido], ignore_index=True)
    
    return df_invertido

def ordenar_por_timestamp(actual, previos, num_previos=50):
    """
    Ordena los partidos actuales y previos por la marca de tiempo de inicio, asegurando que los bloques de partidos previos se alineen con los partidos actuales.
    Args:
        actual (pd.DataFrame): DataFrame con los partidos actuales.
        previos (pd.DataFrame): DataFrame con los partidos previos.
        num_previos (int): Número de partidos previos a considerar para cada partido actual.
    Returns:
        tuple: DataFrames ordenados de partidos actuales y previos.
    """
    # Crear una copia de los DataFrames originales
    actual_copy = actual.copy()
    previos_copy = previos.copy()
    
    # Ordenar actual por startTimeStamp
    actual_copy['original_index'] = actual_copy.index
    actual_copy = actual_copy.sort_values(by='startTimestamp').reset_index(drop=True)
    
    # En lugar de crear un DataFrame vacío, inicializamos una lista para almacenar bloques
    bloques_previos = []
    
    # Para cada fila en actual_ordenado, reorganizar los bloques correspondientes de previos
    for i, row in actual_copy.iterrows():
        print(f'Ordenando fila {i} de {actual_copy.shape[0]}')
        original_idx = int(row['original_index'])  # Convertir a entero
        
        # Calcular los índices de los bloques en previos
        inicio_bloque = int(original_idx * num_previos * 2)  # Convertir a entero
        fin_bloque = int(inicio_bloque + num_previos * 2)    # Convertir a entero
        
        # Verificar límites
        if inicio_bloque >= len(previos_copy) or fin_bloque > len(previos_copy):
            print(f"Advertencia: Índice fuera de rango. Original_idx: {original_idx}, Inicio: {inicio_bloque}, Fin: {fin_bloque}, Len previos: {len(previos_copy)}")
            continue
        
        # Obtener el bloque correspondiente de previos
        bloque_previos = previos_copy.iloc[inicio_bloque:fin_bloque].copy()
        
        # Añadir el bloque a la lista
        bloques_previos.append(bloque_previos)
    
    # Concatenar todos los bloques de una vez al final
    if bloques_previos:
        previos_ordenado = pd.concat(bloques_previos, ignore_index=True)
    else:
        previos_ordenado = pd.DataFrame(columns=previos_copy.columns)
    
    # Eliminar la columna auxiliar
    actual_copy = actual_copy.drop(columns=['original_index'])
    
    return actual_copy, previos_ordenado

def limpieza_final(df, actual):
    """ Limpia y formatea el DataFrame final de partidos, asegurando que los tipos de datos sean correctos y que las columnas tengan los valores adecuados.
    Args:
        df (pd.DataFrame): DataFrame con los partidos.
        actual (bool): Indica si el DataFrame es de partidos actuales o previos.
    Returns:
        pd.DataFrame: DataFrame limpio y formateado.
    """
    print('limpiando datos finales')
    df['idTournament']= df['idTournament'].fillna(0).astype(int)
    df['idSeason']= df['idSeason'].fillna(0).astype(int)
    df['idEvent']= df['idEvent'].fillna(0).astype(int)
    df['round']= df['round'].fillna(0).astype(int)
    if not actual:
        df['idNext']= df['idNext'].fillna(0).astype(int)
    #en los partidos de grand slam: Las rondas clasificatorias de grand slam son al mejor de 3 de juegos.
    # Hay que tener en cuenta, las rondas clasificatorias son las que tienen ronda 1,2,3 o 0
    df.loc[(df['idTournament'].isin([2480]))  & ((df['round'].isin([14,15,19,1,2,0]))), 'periodCount']=3
    df.loc[(df['idTournament'].isin([2480]))  & ~((df['round'].isin([14,15,19,1,2,0]))), 'periodCount']=5
    df.loc[(df['idTournament'].isin([2363]))  & ((df['round'].isin([60,15,19,14]))), 'periodCount']=3
    df.loc[(df['idTournament'].isin([2363]))  & ~((df['round'].isin([60,15,19,14]))), 'periodCount']=5
    #en us open de 2022, las semis estan como ronda 2 y la final está puestas como ronda 1, tenerlo en cuenta
    df.loc[(df['idTournament'].isin([2449]))  & ((df['round'].isin([0,14,15,19]))), 'periodCount']=3
    df.loc[(df['idTournament'].isin([2449]))  & ~((df['round'].isin([0,14,15,19]))), 'periodCount']=5
    df.loc[(df['idTournament'].isin([2449]))  & (df['idSeason']==45261) & (df['round'].isin([1,2])), 'periodCount']=5
    df.loc[(df['idTournament'].isin([2449]))  & ~(df['idSeason']==45261) & (df['round'].isin([1,2])), 'periodCount']=3

    df.loc[(df['idTournament'].isin([2361]))  & ((df['round'].isin([19]))), 'periodCount']=3
    df.loc[(df['idTournament'].isin([2361]))  & ~((df['round'].isin([19]))), 'periodCount']=5
    df.loc[(df['idTournament'].isin([2361]))  & (df['idSeason']==42300) & (df['round'].isin([1,2])), 'periodCount']=5
    df.loc[(df['idTournament'].isin([2361]))  & ~(df['idSeason']==42300) & (df['round'].isin([1,2])), 'periodCount']=3

    df['year']= df['year'].fillna(0).astype(int)

    df['birthDateHome'] = df['birthDateHome'].astype(int)
    df['birthDateAway'] = df['birthDateAway'].astype(int)
    df['ActualRankingHome']= df['ActualRankingHome'].astype(int)
    df['ActualRankingAway']= df['ActualRankingAway'].astype(int)
    df['BestRankingHome']= df['BestRankingHome'].astype(int)
    df['BestRankingAway']= df['BestRankingAway'].astype(int)

    df = df.replace({'groundType': {'Clay':'Red clay', 'Red clay indoor':'Red clay', 'Carpet indoor':'Hardcourt indoor'}})


    return df

def main():  
    """
    Función principal que ejecuta el programa de scraping de partidos de tenis.
    Configura los parámetros globales, descarga los partidos nuevos si es necesario, y procesa los
    partidos actuales y previos.
    """
    global ruta, players, ranking
    #### PARAMETROS QUE RIGEN EL PROGRAMA ####

    ##Se necesita el archivo de ranking, en la carpeta ruta/ranking, si no, ejecutar el otro programa antes


    # ruta: directorio donde se guardan los datos
    # partidos_nuevo: si es true, se descargan los partidos nuevos,el id, sino se cargan de csv
    # nuevo: Si es true, se descargan el acutal, el previos y el ranking nuevo, sino se cargan de csv, por si son parciales
    # num_previos: número de partidos previos a obtener para cada jugador
    # years: años a descargar, por defecto 2021,2022,2023,2024

    # Cambiar el directorio de trabajo al del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Directorio actual:", os.getcwd())

    ruta=f'../data'
    partidos_nuevo=True
    nuevo=True
    num_previos=50
    years=[2021,2022,2023,2024]
    

    instanciar_variables_globales(nuevo)      

    if partidos_nuevo:
        tournaments = scraping_tournaments()
        print(tournaments)
        id_tournaments_seasons = []
        for i in years:
            id_tournaments_seasons.extend(scraping_seasons(tournaments, i))
        id_partidos = scraping_id_matches(id_tournaments_seasons)

        id_partidos_df = pd.DataFrame(id_partidos, columns=['id'])
        id_partidos_df.to_csv(f'{ruta}/id_partidos.csv', index=False)
    else:
        id_partidos=pd.read_csv(f'{ruta}/id_partidos.csv')['id'].values
        id_partidos = list(id_partidos)
        
    
    if nuevo:
        previos = pd.DataFrame(columns=[
                #Identificadores de partido
                'idTournament', 'tournamentName' , 'idSeason', 'idEvent','round' ,'groundType','periodCount',

                #Target
                'winnerCode',

                #referencia al partido posterior
                'idNext',
                #------------------------------------Caracterísitcas a priori----------------------------------------------#
                #Datos temporales del partido
                'startTimestamp','lastMatchTimestamp','year',

                #Datos del jugador local
                'idHome', 'birthDateHome','ActualRankingHome', 'BestRankingHome', 'BestRankingDateHome',
                'HeightHome', 'WeightHome', 'RightHandedHome', 'countryHome',

                #Datos del jugador visitante
                'idAway', 'birthDateAway','ActualRankingAway', 'BestRankingAway', 'BestRankingDateAway',
                'HeightAway', 'WeightAway', 'RightHandedAway', 'countryAway',

                #----------------------------Características a posteriori:-------------------------------------------------------#
                #Estado del partido
                'status', 

                #Datos de resultado del partido
                'homeScore', 'awayScore',

                # Datos de resultados en los sets: -1 si no existen
                'set1performanceHome', 'set1performanceAway',
                'set2performanceHome', 'set2performanceAway',
                'set3performanceHome', 'set3performanceAway',
                'set4performanceHome', 'set4performanceAway',
                'set5performanceHome', 'set5performanceAway',

                # Datos de juegos totales
                'totalGamesHome', 'totalGamesAway',

            ]) 
        actual = pd.DataFrame(columns=[
            #Identificadores de partido
            'idTournament', 'tournamentName','idSeason', 'idEvent', 'round','groundType','periodCount',

            #Target
            'winnerCode',
            #-------------------------------------Probabilidades de la casa de apuestas --------------------------------#
            'ProbabilityHome', 'ProbabilityAway', 
            #------------------------------------Caracterísitcas a priori----------------------------------------------#
            #Datos temporales del partido
            'startTimestamp','year',

            #Datos del jugador local
            'idHome', 'birthDateHome','ActualRankingHome', 'BestRankingHome', 'BestRankingDateHome',
            'HeightHome', 'WeightHome', 'RightHandedHome', 'countryHome',   

            #Datos del jugador visitante
            'idAway', 'birthDateAway','ActualRankingAway', 'BestRankingAway', 'BestRankingDateAway',
            'HeightAway', 'WeightAway', 'RightHandedAway', 'countryAway',

            #----------------------------Características a posteriori:-------------------------------------------------------#
            #Estado del partido
            'status', 
        ])
    else:
        actual=pd.read_csv(f'{ruta}/actual.csv')
        previos=pd.read_csv(f'{ruta}/previos.csv')
    
    #para cada jugador, se obtienen los 50 partidos previos
    num_previos=50
    if(actual.empty):
        inicio_real=0
        id_partidos=id_partidos[inicio_real:]
    else:
        index_buscar= actual.iloc[actual.shape[0]-1]['idEvent']
        empezar=id_partidos.index(index_buscar)
        inicio_real=empezar+1
        id_partidos=id_partidos[(inicio_real):]

    num_partidos=len(id_partidos)
    print('Partidos a extraer',num_partidos)

    for i in range(num_partidos):
        id_event=id_partidos[i]
        print('actual',i+inicio_real, id_event)

        df_partido_actual =scraping_partido(id_event, True)

        if filtrar_partido(df_partido_actual, True):
            print('Actual skipped')
            continue
        
        id_home=int(df_partido_actual.loc[0,'idHome'])
        df_partidos_anteriores_home=get_last_matches(id_home,id_event, num_previos)
        if df_partidos_anteriores_home.shape[0]<num_previos:         
            print('previos home',len(df_partidos_anteriores_home)) 
            continue
        
        id_away=int(df_partido_actual.loc[0,'idAway'])
        df_partidos_anteriores_away=get_last_matches(id_away,id_event, num_previos)
        if df_partidos_anteriores_away.shape[0]<num_previos:          
            print('previos away',len(df_partidos_anteriores_away)) 
            continue

        previos = pd.concat([previos, df_partidos_anteriores_home,df_partidos_anteriores_away], ignore_index=True)
        actual=pd.concat([actual, df_partido_actual],ignore_index=True)
        
        if(previos.shape[0]/actual.shape[0]!=(num_previos*2)):
            print(f"Error: El número de partidos previos ({previos.shape[0]}) no es el esperado ({num_previos*2})")          
            sys.exit(1)

        print(f"Guardando Partido actual, dimension= {previos.shape[0]/actual.shape[0]}, no apagar")
        previos.to_csv(f'{ruta}/previos.csv', index=False)
        actual.to_csv(f'{ruta}/actual.csv',index=False)
        players.to_csv(f'{ruta}/players.csv',index=False)
        ranking.to_csv(f'{ruta}/ranking.csv',index=False)
        print("Partido ya guardado")
        print('-------------------------------')
    
    
    previos_imputado=impute_player_data(previos)
    actual_imputado=impute_player_data(actual)
    previos_reorganizado=reorganizar_partidos(actual_imputado,previos_imputado, num_previos)
    previos_invertido = invertir_bloques(previos_reorganizado, num_previos)
    actual_ordenado, previos_ordenado= ordenar_por_timestamp(actual_imputado, previos_invertido, num_previos)

    actual_final = limpieza_final(actual_ordenado, True)
    previos_final = limpieza_final(previos_ordenado, False)
    actual_final.to_csv(f'{ruta}/completo/actual_final.csv', index=False)
    previos_final.to_csv(f'{ruta}/completo/previos_final.csv', index=False)
            
if __name__ == "__main__":
    main()