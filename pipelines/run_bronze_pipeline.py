# This code is responsible for running the bronze pipeline
# The bronze pipeline consists in extracting data from the Surfline API. We save the data in a bronze layer, separating by entity so we have : 
# surfline_bronze_rankings
# surfline_bronze_wind
# surfline_bronze_sunlight
# surfline_bronze_swells
# surfline_bronze_tides
# surfline_bronze_surf_height

import yaml
import argparse
from datetime import datetime, timedelta
import time
# Adiciona o diretório raiz do projeto ao sys.path
import sys
from pathlib import Path

# Garante que o diretório raiz do projeto esteja no sys.path quando o script é executado diretamente
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.surfline_extractor import extract_surfline_entity

# Agora o import funciona mesmo chamando: python pipelines/run_bronze_pipeline.py
def load_config(config_path='config/config.yaml'):
    """Carrega o arquivo de configuração YAML."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Função principal que orquestra a execução do pipeline."""
    parser = argparse.ArgumentParser(description="Pipeline para extração de dados da camada Bronze do Surfline.")
    parser.add_argument('--entity', type=str, help="Extrair apenas uma entidade específica (ex: 'wind').")
    parser.add_argument('--start_date', type=str, help="Data de início para uma extração pontual ('YYYY-MM-DD').")
    
    args = parser.parse_args()
    config = load_config()

    if args.entity:
        entities_to_process = [args.entity]
    else:
        entities_to_process = list(config['entities'].keys())

    if args.start_date:
        start_date = args.start_date
        # Para uma extração pontual, pegamos um período de 16 dias
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
    else:
        # Período completo do projeto por padrão
        start_date = config['project']['start_date']
        end_date = config['project']['end_date']
        
    print(f">>> INICIANDO JOB BRONZE | PERÍODO: {start_date} a {end_date} <<<")

    for entity in entities_to_process:
        if entity not in config['entities']:
            print(f"Erro: Entidade '{entity}' não encontrada no config.yaml. Pulando.")
            continue
        extract_surfline_entity(entity, config, start_date, end_date)
        print('15 seconds pause for each entity')
        time.sleep(15)

    print("\n>>> JOB BRONZE FINALIZADO! <<<")

if __name__ == "__main__":
    main()