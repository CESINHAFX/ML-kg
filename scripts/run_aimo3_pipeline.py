"""
Orquestrador AIMO3  Pipeline Completo
Executa scraping  análise  report
"""

import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd_str, description):
    """Executa comando e registra resultado."""
    logger.info(f"\n{'='*70}")
    logger.info(f" {description}")
    logger.info(f"{'='*70}")
    try:
        result = subprocess.run(cmd_str, shell=True, check=True)
        logger.info(f" {description} CONCLUÍDO")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f" {description} FALHOU com código {e.returncode}")
        return False

def main():
    """Orquestra todo o pipeline."""
    
    logger.info(" INICIANDO PIPELINE AIMO3")
    
    # Etapas
    steps = [
        ('python scripts/fetch_aimo3_notebooks.py', '1 Web Scraping dos 3 Notebooks'),
        ('python scripts/analyze_aimo3_notebooks.py', '2 Análise & Preenchimento de Templates'),
    ]
    
    for cmd, desc in steps:
        success = run_command(cmd, desc)
        if not success:
            logger.warning(f" Parando pipeline após {desc}")
            break
    
    logger.info("\n" + "="*70)
    logger.info(" PIPELINE COMPLETO")
    logger.info("="*70)
    logger.info("\n Saída disponível em:")
    logger.info("   - HTML bruto: data_sources/raw/kaggle/aimo3_notebooks/html/")
    logger.info("   - JSON metadados: data_sources/raw/kaggle/aimo3_notebooks/json/")
    logger.info("   - Análises JSON: data_sources/processed/aimo3_analysis/filled/")
    logger.info("   - Report consolidado: data_sources/processed/aimo3_analysis/REPORT.md")
    logger.info("   - Logs: data_sources/logs/aimo3_scraping.log\n")

if __name__ == '__main__':
    main()
