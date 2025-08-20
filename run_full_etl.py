#!/usr/bin/env python3
"""
================================================================================
METEOMATICS ETL AUTOMATION PIPELINE
================================================================================

Script principal para automação completa do pipeline ETL:
1. Extração de dados (Bronze layer)
2. Transformação dbt (Silver layer) 
3. Modelagem Star Schema (Gold layer)
4. Criação de Data Marts especializados

Uso:
    python run_full_etl.py [--config CONFIG_PATH] [--skip-bronze] [--skip-dbt]
    
Exemplos:
    python run_full_etl.py                           # Pipeline completo
    python run_full_etl.py --skip-bronze             # Só dbt (silver/gold/marts)
    python run_full_etl.py --config custom.yaml      # Config customizado

Autor: Meteomatics Team
Data: 2025-08-20
"""

import os
import sys
import yaml
import argparse
import logging
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd

# ================================================================================
# CONFIGURAÇÃO DE LOGGING
# ================================================================================

def setup_logging():
    """Configura logging para o pipeline"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f'logs/etl_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('meteomatics_etl')

# ================================================================================
# CONFIGURAÇÃO E VALIDAÇÃO
# ================================================================================

def load_config(config_path: str = 'config/config.yaml') -> dict:
    """Carrega e valida arquivo de configuração"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"✅ Configuração carregada: {config_path}")
        logger.info(f"📊 Projeto: {config['project']['name']} v{config['project']['version']}")
        
        return config
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {e}")
        sys.exit(1)

def validate_environment():
    """Valida se o ambiente está configurado corretamente"""
    logger.info("🔍 Validando ambiente...")
    
    # Verificar se está no venv
    if 'VIRTUAL_ENV' not in os.environ:
        logger.warning("⚠️  Virtual environment não detectado")
    
    # Verificar estrutura de diretórios
    required_dirs = ['data', 'config', 'dbt_meteomatics', 'logs']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            logger.info(f"📁 Criando diretório: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
    
    # Verificar dbt
    try:
        result = subprocess.run(['dbt', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ dbt instalado e funcionando")
        else:
            logger.error("❌ dbt não está funcionando corretamente")
            sys.exit(1)
    except FileNotFoundError:
        logger.error("❌ dbt não encontrado. Instale com: pip install dbt-duckdb")
        sys.exit(1)

# ================================================================================
# ETAPAS DO PIPELINE
# ================================================================================

def run_bronze_extraction(config: dict) -> bool:
    """Executa extração de dados para camada Bronze"""
    logger.info("🥉 INICIANDO CAMADA BRONZE")
    logger.info("=" * 50)
    
    try:
        # Executar pipeline bronze existente
        result = subprocess.run([
            'python', 'pipelines/run_bronze_pipeline.py'
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            logger.info("✅ Camada Bronze executada com sucesso")
            return True
        else:
            logger.error(f"❌ Erro na camada Bronze: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao executar camada Bronze: {e}")
        return False

def run_dbt_pipeline(config: dict) -> bool:
    """Executa pipeline dbt (Silver + Gold)"""
    logger.info("🥈🥇 INICIANDO PIPELINE DBT")
    logger.info("=" * 50)
    
    try:
        dbt_dir = config['dbt']['project_dir']
        profiles_dir = config['dbt']['profiles_dir']
        
        # Debug dbt
        logger.info("🔍 Verificando configuração dbt...")
        debug_result = subprocess.run([
            'dbt', 'debug', '--profiles-dir', profiles_dir
        ], capture_output=True, text=True, cwd=dbt_dir)
        
        if debug_result.returncode != 0:
            logger.error(f"❌ dbt debug falhou: {debug_result.stderr}")
            return False
        
        # Executar modelos dbt
        logger.info("🚀 Executando modelos dbt...")
        run_result = subprocess.run([
            'dbt', 'run', '--profiles-dir', profiles_dir
        ], capture_output=True, text=True, cwd=dbt_dir)
        
        if run_result.returncode == 0:
            logger.info("✅ Pipeline dbt executado com sucesso")
            logger.info(f"📊 Output: {run_result.stdout}")
            return True
        else:
            logger.error(f"❌ Erro no pipeline dbt: {run_result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao executar pipeline dbt: {e}")
        return False

def run_dbt_tests(config: dict) -> bool:
    """Executa testes de qualidade dbt"""
    logger.info("🧪 EXECUTANDO TESTES DE QUALIDADE")
    logger.info("=" * 30)
    
    try:
        dbt_dir = config['dbt']['project_dir'] 
        profiles_dir = config['dbt']['profiles_dir']
        
        test_result = subprocess.run([
            'dbt', 'test', '--profiles-dir', profiles_dir
        ], capture_output=True, text=True, cwd=dbt_dir)
        
        if test_result.returncode == 0:
            logger.info("✅ Todos os testes passaram")
            return True
        else:
            logger.warning(f"⚠️  Alguns testes falharam: {test_result.stdout}")
            return True  # Continuar mesmo com falhas nos testes
            
    except Exception as e:
        logger.warning(f"⚠️  Erro ao executar testes: {e}")
        return True  # Continuar mesmo com erro nos testes

def generate_data_summary(config: dict) -> bool:
    """Gera resumo dos dados processados"""
    logger.info("📊 GERANDO RESUMO DOS DADOS")
    logger.info("=" * 30)
    
    try:
        import duckdb
        
        conn = duckdb.connect('data/dbt_meteomatics.duckdb')
        
        # Contar registros por tabela
        tables = conn.execute("SHOW TABLES").fetchall()
        
        summary = {
            'silver_tables': {},
            'gold_tables': {},
            'total_records': 0
        }
        
        for table_tuple in tables:
            table = table_tuple[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            summary['total_records'] += count
            
            if table.startswith('stg_'):
                summary['silver_tables'][table] = count
            elif table.startswith('dim_') or table.startswith('fact_'):
                summary['gold_tables'][table] = count
        
        # Log do resumo
        logger.info(f"📋 RESUMO FINAL:")
        logger.info(f"   🥈 Silver: {len(summary['silver_tables'])} tabelas")
        for table, count in summary['silver_tables'].items():
            logger.info(f"      ✅ {table}: {count:,} registros")
            
        logger.info(f"   🥇 Gold: {len(summary['gold_tables'])} tabelas") 
        for table, count in summary['gold_tables'].items():
            logger.info(f"      ✅ {table}: {count:,} registros")
            
        logger.info(f"   📊 Total: {summary['total_records']:,} registros processados")
        
        # Salvar resumo em arquivo
        with open(f'logs/pipeline_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml', 'w') as f:
            yaml.dump(summary, f)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar resumo: {e}")
        return False

# ================================================================================
# FUNÇÃO PRINCIPAL
# ================================================================================

def main():
    """Função principal do pipeline ETL"""
    
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(
        description='Pipeline ETL automatizado Meteomatics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_full_etl.py                     # Pipeline completo
  python run_full_etl.py --skip-bronze       # Pular extração bronze  
  python run_full_etl.py --skip-dbt          # Só executar bronze
  python run_full_etl.py --config custom.yaml # Config customizado
        """
    )
    
    parser.add_argument(
        '--config', 
        default='config/config.yaml',
        help='Caminho para arquivo de configuração (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--skip-bronze',
        action='store_true', 
        help='Pular extração da camada bronze'
    )
    
    parser.add_argument(
        '--skip-dbt',
        action='store_true',
        help='Pular execução do pipeline dbt' 
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Pular testes de qualidade'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    global logger
    logger = setup_logging()
    
    # Banner inicial
    logger.info("🌊" * 20)
    logger.info("🌊 METEOMATICS ETL PIPELINE AUTOMATION 🌊") 
    logger.info("🌊" * 20)
    logger.info(f"⏰ Início: {datetime.now()}")
    
    # Carregar configuração
    config = load_config(args.config)
    
    # Validar ambiente
    validate_environment()
    
    # Executar pipeline
    success = True
    start_time = datetime.now()
    
    try:
        # 1. Camada Bronze (Extração)
        if not args.skip_bronze:
            bronze_success = run_bronze_extraction(config)
            success = success and bronze_success
        else:
            logger.info("⏭️  Pulando camada Bronze")
        
        # 2. Pipeline dbt (Silver + Gold)
        if not args.skip_dbt and success:
            dbt_success = run_dbt_pipeline(config)
            success = success and dbt_success
        else:
            if args.skip_dbt:
                logger.info("⏭️  Pulando pipeline dbt")
        
        # 3. Testes de qualidade
        if not args.skip_tests and success:
            run_dbt_tests(config)
        else:
            if args.skip_tests:
                logger.info("⏭️  Pulando testes")
        
        # 4. Resumo final
        if success:
            generate_data_summary(config)
        
    except KeyboardInterrupt:
        logger.warning("🛑 Pipeline interrompido pelo usuário")
        success = False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        success = False
    
    # Resultado final
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("🌊" * 20)
    if success:
        logger.info("🎉 PIPELINE EXECUTADO COM SUCESSO!")
    else:
        logger.error("❌ PIPELINE FALHOU")
    
    logger.info(f"⏱️  Duração: {duration}")
    logger.info(f"🏁 Fim: {end_time}")
    logger.info("🌊" * 20)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
