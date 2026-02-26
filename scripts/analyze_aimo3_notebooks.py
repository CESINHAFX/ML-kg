"""
Script de Análise  Preenche Templates com Dados Extraídos
"""

import json
from pathlib import Path
from datetime import datetime
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_scraped_metadata(notebook_id):
    """Carrega JSON extraído do scraping."""
    path = Path(f'data_sources/raw/kaggle/aimo3_notebooks/json/{notebook_id}_metadata.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_json_from_template(scraped_data):
    """Cria análise JSON com dados extraídos."""
    metadata = scraped_data['metadata']
    params = scraped_data['parameters_extracted']
    
    analysis = {
        'notebook_id': scraped_data['notebook_id'],
        'metadata': {
            'title': metadata.get('title', 'N/A'),
            'author': metadata.get('author', 'N/A'),
            'url': metadata.get('url', 'N/A'),
            'date': metadata.get('date', 'N/A'),
            'fetch_date': metadata.get('fetch_date', datetime.now().isoformat()),
            'license': 'CC0 or proprietary'
        },
        'parameters_extracted': params,
        'stats': scraped_data['stats'],
        'status': 'PENDING_REVIEW',
        'prompts_detected': len(scraped_data['prompts_extracted']),
        'code_cells_count': len(scraped_data['code_cells']),
        'markdown_cells_count': len(scraped_data['markdown_cells'])
    }
    
    return analysis

def save_analysis(notebook_id, analysis):
    """Salva análise JSON."""
    json_path = Path(f'data_sources/processed/aimo3_analysis/filled/{notebook_id}_analysis.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    logger.info(f" Análise JSON salva: {json_path}")

def analyze_all_notebooks():
    """Analisa todos os 3 notebooks."""
    logger.info("=" * 70)
    logger.info("ANALISANDO NOTEBOOKS EXTRAÍDOS")
    logger.info("=" * 70)
    
    notebook_ids = [
        'aimo3_masa_pipeline',
        'aimo3_frieder_submission',
        'aimo3_pranshu_ensemble'
    ]
    
    for nb_id in notebook_ids:
        logger.info(f"\n Processando: {nb_id}")
        try:
            scraped_data = load_scraped_metadata(nb_id)
            analysis = create_json_from_template(scraped_data)
            save_analysis(nb_id, analysis)
            logger.info(f" {nb_id} analisado com sucesso")
        except Exception as e:
            logger.error(f" Erro ao processar {nb_id}: {e}")

def generate_report():
    """Gera report consolidado."""
    logger.info("=" * 70)
    logger.info("GERANDO REPORT CONSOLIDADO")
    logger.info("=" * 70)
    
    report = "# Análise Consolidada: AIMO3 Top 3 Notebooks\n\n"
    report += f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    report += "## Status da Coleta\n\n"
    report += "| Notebook | Autor | Status | Células | Parâmetros |\n"
    report += "|---|---|---|---|---|\n"
    
    notebook_ids = [
        'aimo3_masa_pipeline',
        'aimo3_frieder_submission',
        'aimo3_pranshu_ensemble'
    ]
    
    for nb_id in notebook_ids:
        try:
            json_path = Path(f'data_sources/processed/aimo3_analysis/filled/{nb_id}_analysis.json')
            with open(json_path) as f:
                data = json.load(f)
            
            author = data['metadata'].get('author', 'N/A')
            cells = data['code_cells_count']
            params = len(data['parameters_extracted'])
            
            report += f"| {nb_id} | {author} |  OK | {cells} | {params} |\n"
        except:
            report += f"| {nb_id} | ? |  ERRO |  |  |\n"
    
    report += "\n## Próximas Ações\n"
    report += "- [ ] Revisar parâmetros extraídos\n"
    report += "- [ ] Preencher análise qualitativa (O que/Por que)\n"
    report += "- [ ] Validar prompts detectados\n"
    report += "- [ ] Comparar notebooks e resultados\n"
    
    report_path = Path('data_sources/processed/aimo3_analysis/REPORT.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f" Report salvo: {report_path}")
    print("\n" + report)

if __name__ == '__main__':
    if '--report' in sys.argv:
        generate_report()
    else:
        analyze_all_notebooks()
        generate_report()
