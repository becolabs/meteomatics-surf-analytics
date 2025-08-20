import yaml
import argparse
import pandas as pd
import os
# Importamos as funções que vamos reutilizar
from src.surfline_extractor import fetch_single_period

def load_config(config_path='config/config.yaml'):
    """Carrega o arquivo de configuração YAML."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """
    Ferramenta de linha de comando para extrair um período faltante
    e inseri-lo em um arquivo CSV bronze existente.
    """
    parser = argparse.ArgumentParser(description="Ferramenta para corrigir falhas na ingestão da camada Bronze do Surfline.")
    parser.add_argument('entity', type=str, help="A entidade a ser corrigida (ex: 'wind', 'swells').")
    parser.add_argument('start_date', type=str, help="A data de início do período faltante ('YYYY-MM-DD').")
    
    args = parser.parse_args()
    config = load_config()
    
    entity_name = args.entity
    start_date = args.start_date

    if entity_name not in config['entities']:
        print(f"❌ Erro: Entidade '{entity_name}' não encontrada no config.yaml.")
        return

    print(f"--- Iniciando reparo para entidade '{entity_name}' no período de '{start_date}' ---")

    # --- 1. Extrair o período faltante ---
    entity_config = config['entities'][entity_name]
    api_config = config['api']
    base_url = api_config['base_url'] + entity_name
    params = {
        'spotId': api_config['spot_id'],
        'days': entity_config.get('params', {}).get('days', 16),
        'intervalHours': 1,
        'start': start_date,
        'accesstoken': api_config['access_token']
    }
    params.update(entity_config.get('params', {}))

    df_dados_novos = fetch_single_period(base_url, params, entity_config)

    if df_dados_novos is None:
        print("❌ A extração do período faltante falhou. O arquivo não será modificado.")
        return
        
    print(f"✅ {len(df_dados_novos)} novos registros extraídos com sucesso.")

    # --- 2. Carregar, Juntar e Salvar ---
    caminho_arquivo = os.path.join(config['project']['output_dir'], f'surfline_bronze_{entity_name}.csv')
    
    try:
        print(f"Carregando arquivo existente: {caminho_arquivo}")
        df_existente = pd.read_csv(caminho_arquivo)
        
        df_combinado = pd.concat([df_existente, df_dados_novos], ignore_index=True)
        print(f"Combinado! Total de registros antes da limpeza: {len(df_combinado)}")

        # --- 3. Reaplicar as transformações e limpeza ---
        # Lógica de timestamp
        timestamp_col = 'total_timestamp' if 'total_timestamp' in df_combinado.columns else 'timestamp'
        if timestamp_col in df_combinado.columns:
            df_combinado['datetime'] = pd.to_datetime(df_combinado[timestamp_col], unit='s', utc=True)
            df_combinado['datetime'] = df_combinado['datetime'].dt.tz_convert('America/Sao_Paulo')
        
        # Lógica de sunlight
        if entity_name == 'sunlight':
            for col in ['midnight', 'dawn', 'sunrise', 'sunset', 'dusk']:
                if col in df_combinado.columns:
                    df_combinado[col] = pd.to_datetime(df_combinado[col], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
        
        # Lógica para remover duplicatas e reordenar
        date_col_ref = 'datetime'
        if entity_name == 'sunlight':
            date_col_ref = 'midnight'
        elif entity_name == 'swells': # Swells pode ter múltiplos swells por timestamp
             # Para swells, a duplicata é a combinação do timestamp E das características do swell
            subset_cols = [col for col in df_combinado.columns if col not in ['utcOffset', 'total_utcOffset']]
            df_combinado.drop_duplicates(subset=subset_cols, inplace=True)
        else:
            df_combinado.drop_duplicates(subset=[date_col_ref], inplace=True)
            
        df_combinado.sort_values(by=date_col_ref, inplace=True)
        
        # --- 4. Salvar ---
        df_combinado.to_csv(caminho_arquivo, index=False)
        print(f"\n✅ Arquivo '{caminho_arquivo}' foi corrigido e salvo com sucesso!")
        print(f"Total final de registros: {len(df_combinado)}")

    except FileNotFoundError:
        print(f"⚠️ Aviso: Arquivo original não encontrado. Salvando um novo arquivo apenas com os dados do período extraído.")
        # Se o arquivo não existir, apenas salva o novo DataFrame com o tratamento de data
        timestamp_col = 'total_timestamp' if 'total_timestamp' in df_dados_novos.columns else 'timestamp'
        df_dados_novos['datetime'] = pd.to_datetime(df_dados_novos[timestamp_col], unit='s', utc=True)
        df_dados_novos['datetime'] = df_dados_novos['datetime'].dt.tz_convert('America/Sao_Paulo')
        df_dados_novos.to_csv(caminho_arquivo, index=False)
        print(f"✅ Novo arquivo '{caminho_arquivo}' criado com sucesso.")
    except Exception as e:
        print(f"❌ Ocorreu um erro ao processar e salvar o arquivo: {e}")


if __name__ == "__main__":
    main()