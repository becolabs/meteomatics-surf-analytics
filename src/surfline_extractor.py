import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
from tqdm import tqdm
import os
import json
import gzip
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'Referer': 'https://www.surfline.com/'
}

def gerar_datas_de_inicio(data_inicio_str, data_fim_str, intervalo_dias=16):
    data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
    datas_geradas = []
    data_atual = data_inicio
    while data_atual <= data_fim:
        datas_geradas.append(data_atual.strftime('%Y-%m-%d'))
        data_atual += timedelta(days=intervalo_dias)
    return datas_geradas

def _save_raw_payload(raw_dir: str, entity: str, start_date: str, response_json: dict, status_code: int, duration_ms: int):
    """Salva JSON bruto + metadados (landing)."""
    # Validação simples de formato YYYY-MM-DD
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', start_date):
        print(f"[AVISO] start_date inválida '{start_date}' – ignorando salvamento raw desta requisição.")
        return None
    # Estrutura: raw_dir/entity/start=YYYY-MM-DD/
    base_path = os.path.join(raw_dir, entity, f"start={start_date}")
    os.makedirs(base_path, exist_ok=True)
    payload_bytes = json.dumps(response_json, ensure_ascii=False).encode('utf-8')
    sha256_hash = hashlib.sha256(payload_bytes).hexdigest()
    raw_file = os.path.join(base_path, 'response.json.gz')
    with gzip.open(raw_file, 'wb') as gz:
        gz.write(payload_bytes)
    meta = {
        'entity': entity,
        'start_date': start_date,
        'saved_at_utc': datetime.now(timezone.utc).isoformat(),
        'status_code': status_code,
        'hash_sha256': sha256_hash,
        'raw_file': raw_file,
        'duration_ms': duration_ms,
        'records_estimated': None  # preenchido depois se disponível
    }
    meta_file = os.path.join(base_path, 'response.meta.json')
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta

def fetch_single_period(base_url: str, params: dict, entity_config: dict, *, capture_raw: bool=False, raw_dir: str|None=None, entity_name: str|None=None):
    """
    Busca dados para UM ÚNICO período e retorna um dicionário com o status.
    """
    start_date = params.get('start', 'Data Desconhecida')
    t0 = time.time()
    try:
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
        time.sleep(2)
        duration_ms = int((time.time() - t0) * 1000)

        # Captura bruta se habilitado (independente de ser 200 para auditoria, mas comum filtrar só 200)
        meta = None
        if capture_raw and raw_dir and entity_name and response.headers.get('Content-Type','').startswith('application/json'):
            try:
                raw_json_for_save = response.json()
                meta = _save_raw_payload(raw_dir, entity_name, start_date, raw_json_for_save, response.status_code, duration_ms)
            except Exception as e:  # falha de parse não deve abortar
                meta = {'error_raw_save': str(e)}

        if response.status_code == 200:
            try:
                dados_json = response.json()
            except Exception as e:
                return {'status': 'failure', 'start_date': start_date, 'error': f'JSON parse error: {e}', 'raw_meta': meta}

            path = dados_json
            for key in entity_config['json_path']:
                path = path.get(key, []) if isinstance(path, dict) else []

            normalize_cfg = entity_config.get('normalize_config', {})
            df_periodo = pd.json_normalize(path, **normalize_cfg)

            if meta and isinstance(meta, dict) and 'records_estimated' in meta:
                meta['records_estimated'] = len(df_periodo)

            if not df_periodo.empty:
                return {
                    'status': 'success',
                    'start_date': start_date,
                    'data': df_periodo,
                    'duration_ms': duration_ms,
                    'raw_meta': meta
                }
            else:
                return {'status': 'failure', 'start_date': start_date, 'error': 'JSON sem registros', 'duration_ms': duration_ms, 'raw_meta': meta}
        else:
            error_message = f"Status Code: {response.status_code}"
            return {'status': 'failure', 'start_date': start_date, 'error': error_message, 'duration_ms': duration_ms, 'raw_meta': meta}

    except Exception as e:
        # Se ocorrer um timeout ou outro erro, retorna falha com o motivo
        return {'status': 'failure', 'start_date': start_date, 'error': str(e), 'duration_ms': int((time.time() - t0) * 1000)}
    
    # Caso não entre em nenhuma condição acima (ex: JSON vazio)
    return {'status': 'failure', 'start_date': start_date, 'error': 'Nenhum dado retornado ou erro desconhecido.'}


def extract_surfline_entity(entity_name: str, config: dict, start_date: str, end_date: str):
    """
    Extrai dados históricos usando um pool de threads e reporta falhas no final.
    """
    print(f"\n{'='*50}\nINICIANDO EXTRAÇÃO CONCORRENTE DA ENTIDADE: {entity_name.upper()}\n{'='*50}")

    entity_config = config['entities'][entity_name]
    api_config = config['api']
    project_cfg = config.get('project', {})
    capture_raw = project_cfg.get('capture_raw', False)
    raw_dir = project_cfg.get('raw_dir', os.path.join('data', 'landing', 'surfline_raw')) if capture_raw else None
    
    lista_de_datas = gerar_datas_de_inicio(start_date, end_date)
    base_url = api_config['base_url'] + entity_name
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for data_inicio in lista_de_datas:
            params = {
                'spotId': api_config['spot_id'],
                'days': entity_config.get('params', {}).get('days', 16),
                'intervalHours': 1,
                'start': data_inicio,
                'accesstoken': api_config['access_token']
            }
            params.update(entity_config.get('params', {}))
            futures.append(
                executor.submit(
                    fetch_single_period,
                    base_url,
                    params,
                    entity_config,
                    capture_raw=capture_raw,
                    raw_dir=raw_dir,
                    entity_name=entity_name
                )
            )

        for future in tqdm(as_completed(futures), total=len(futures), desc=f"Buscando '{entity_name}'"):
            result = future.result()
            if result:
                all_results.append(result)

    # --- NOVO: Processamento dos resultados e separação de sucessos e falhas ---
    lista_de_dataframes = []
    failed_dates = []
    ingestion_log_rows = []
    for result in all_results:
        if result['status'] == 'success':
            df_local = result['data']
            lista_de_dataframes.append(df_local)
            ingestion_log_rows.append({
                'entity': entity_name,
                'start_date': result.get('start_date'),
                'status': 'success',
                'rows': len(df_local),
                'duration_ms': result.get('duration_ms'),
                'raw_file': (result.get('raw_meta') or {}).get('raw_file') if result.get('raw_meta') else None,
                'ingested_at_utc': datetime.now(timezone.utc).isoformat()
            })
        else:
            failed_dates.append(result)
            ingestion_log_rows.append({
                'entity': entity_name,
                'start_date': result.get('start_date'),
                'status': 'failure',
                'rows': 0,
                'duration_ms': result.get('duration_ms'),
                'error': result.get('error'),
                'raw_file': (result.get('raw_meta') or {}).get('raw_file') if result.get('raw_meta') else None,
                'ingested_at_utc': datetime.now(timezone.utc).isoformat()
            })

    df_completo = None
    if not lista_de_dataframes:
        print(f"Nenhum dado foi extraído com sucesso para a entidade '{entity_name}'.")
    else:
        print(f"\nConsolidando e salvando dados para '{entity_name}'...")
        df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
        # ... (resto da lógica de limpeza e salvamento continua igual)
        timestamp_col = 'total_timestamp' if 'total_timestamp' in df_completo.columns else 'timestamp'
        if timestamp_col in df_completo.columns:
             df_completo['datetime'] = pd.to_datetime(df_completo[timestamp_col], unit='s', utc=True)
             df_completo['datetime'] = df_completo['datetime'].dt.tz_convert('America/Sao_Paulo')
        if entity_name == 'sunlight':
            for col in ['midnight', 'dawn', 'sunrise', 'sunset', 'dusk']:
                df_completo[col] = pd.to_datetime(df_completo[col], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
        
        data_final_filtro = pd.to_datetime(f"{end_date} 23:59:59").tz_localize('America/Sao_Paulo')
        date_col_ref = 'midnight' if entity_name == 'sunlight' else 'datetime'
        df_completo = df_completo[df_completo[date_col_ref] <= data_final_filtro]

        output_dir = config['project']['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        # Trocar csv por parquet
        #caminho_arquivo = os.path.join(output_dir, f'surfline_bronze_{entity_name}.csv')
        #df_completo.to_csv(caminho_arquivo, index=False)
        nome_arquivo = f'surfline_bronze_{entity_name}.parquet'
        caminho_arquivo = os.path.join(output_dir, nome_arquivo)
        df_completo.to_parquet(caminho_arquivo, index=False)
        print(f"✅ Dados de '{entity_name}' salvos com sucesso em '{caminho_arquivo}'!")
    # Estatísticas rápidas
    linhas, colunas = df_completo.shape
    null_total = int(df_completo.isna().sum().sum())
    print(f"Resumo -> linhas: {linhas:,} | colunas: {colunas} | nulos totais: {null_total:,}")

    # --- NOVO: Relatório de Falhas no Final ---
    if failed_dates:
        print("\n--- ⚠️ RELATÓRIO DE FALHAS ---")
        print("Os seguintes períodos não puderam ser extraídos e precisam ser reprocessados:")
        for failure in failed_dates:
            # Trunca a mensagem de erro para não poluir a tela
            error_message = (failure['error'][:120] + '...') if len(failure['error']) > 120 else failure['error']
            print(f"  - Data de Início: {failure['start_date']}, Erro: {error_message}")
        print("\nUse o script 'pipelines/fix_ingest.py' para reprocessar estas datas.")
    else:
        print("\n--- ✅ Nenhuma falha detectada durante a extração. ---")

    # Salva/atualiza ingestion log (Parquet) se houver capture_raw ou sempre (útil para auditoria)
    try:
        if ingestion_log_rows:
            log_df_new = pd.DataFrame(ingestion_log_rows)
            log_dir = raw_dir if capture_raw and raw_dir else os.path.join('data', 'landing')
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, '_ingestion_log.parquet')
            if os.path.exists(log_path):
                log_existing = pd.read_parquet(log_path)
                log_df_full = pd.concat([log_existing, log_df_new], ignore_index=True)
            else:
                log_df_full = log_df_new
            log_df_full.to_parquet(log_path, index=False)
    except Exception as e:
        print(f"Aviso: Falha ao registrar ingestion log: {e}")

    return df_completo