"""
Script de Scraping para Notebooks AIMO3
Extrai metadados, código, parâmetros e prompts dos 3 notebooks AIMO3 prioritários.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_sources/logs/aimo3_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path='data_sources/configs/aimo3_config.json'):
    """Carrega arquivo de configuração JSON."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo de config não encontrado: {config_path}")
        sys.exit(1)

def setup_directories():
    """Cria estrutura de diretórios necessária."""
    dirs = [
        Path('data_sources/raw/kaggle/aimo3_notebooks/html'),
        Path('data_sources/raw/kaggle/aimo3_notebooks/json'),
        Path('data_sources/logs')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f" Diretório criado/verificado: {d}")

def fetch_with_retry(url, headers, max_retries=3, timeout=15):
    """Fetch com retry e backoff exponencial."""
    for attempt in range(max_retries):
        try:
            logger.info(f"[Tentativa {attempt + 1}/{max_retries}] Buscando: {url}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f" Sucesso! Status: {response.status_code}")
            return response.text
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na tentativa {attempt + 1}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Erro de conexão na tentativa {attempt + 1}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP {response.status_code}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Erro inesperado na tentativa {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            wait_time = 3 * (2 ** attempt)
            logger.info(f"Aguardando {wait_time}s antes de retry...")
            time.sleep(wait_time)
    
    logger.error(f"Falha após {max_retries} tentativas para {url}")
    return None

def extract_number(text):
    """Extrai número de string."""
    match = re.search(r'\d+', text)
    return match.group(0) if match else 'N/A'

def parse_notebook_metadata(html, config):
    """Parse metadados do notebook."""
    soup = BeautifulSoup(html, 'html.parser')
    metadata = {}
    
    # JSON-LD
    json_ld_script = soup.find('script', type='application/ld+json')
    if json_ld_script:
        try:
            ld_json = json.loads(json_ld_script.string)
            metadata['title'] = ld_json.get('name', 'N/A')
            metadata['author'] = ld_json.get('author', {}).get('name', 'N/A')
            metadata['date'] = ld_json.get('datePublished', 'N/A')
        except:
            pass
    
    # Fallback CSS selectors
    if not metadata.get('title'):
        for selector in config['selectors']['title']:
            title_elem = soup.select_one(selector)
            if title_elem:
                metadata['title'] = title_elem.get_text(strip=True)
                break
        if not metadata.get('title'):
            metadata['title'] = 'N/A'
    
    if not metadata.get('author'):
        for selector in config['selectors']['author']:
            author_elem = soup.select_one(selector)
            if author_elem:
                metadata['author'] = author_elem.get_text(strip=True)
                break
        if not metadata.get('author'):
            metadata['author'] = 'N/A'
    
    metadata['date'] = metadata.get('date', 'N/A')
    metadata['views'] = 'N/A'
    metadata['votes'] = 'N/A'
    
    return metadata

def extract_code_cells(html, config):
    """Extrai todas as células de código."""
    soup = BeautifulSoup(html, 'html.parser')
    code_cells = []
    
    for i, selector in enumerate(config['selectors']['code_cells']):
        cells = soup.select(selector)
        for idx, cell in enumerate(cells):
            code = cell.get_text(strip=True)
            if code and len(code) > 5:
                code_cells.append({
                    'cell_id': f"code_{len(code_cells)}",
                    'order': len(code_cells),
                    'code': code[:5000]
                })
    
    logger.info(f"   {len(code_cells)} células de código extraídas")
    return code_cells

def extract_markdown_cells(html, config):
    """Extrai blocos de Markdown."""
    soup = BeautifulSoup(html, 'html.parser')
    md_cells = []
    
    for selector in config['selectors']['markdown_cells']:
        cells = soup.select(selector)
        for idx, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            if text and len(text) > 10:
                md_cells.append({
                    'cell_id': f"md_{len(md_cells)}",
                    'order': len(md_cells),
                    'text': text[:2000]
                })
    
    logger.info(f"   {len(md_cells)} células Markdown extraídas")
    return md_cells

def extract_parameters(code_cells, config):
    """Extrai parâmetros usando regex."""
    all_code = ' '.join([cell['code'] for cell in code_cells])
    parameters = {}
    
    patterns = config['regex_patterns']
    
    for param_name, pattern in patterns.items():
        if 'pass_at' in param_name:
            matches = re.findall(pattern, all_code, re.IGNORECASE)
            for k, value in matches:
                parameters[f'pass_at_{k}'] = float(value)
        else:
            match = re.search(pattern, all_code, re.IGNORECASE)
            if match:
                try:
                    if param_name in ['n_samples', 'max_tokens', 'seed']:
                        parameters[param_name] = int(match.group(1))
                    elif param_name in ['temperature', 'accuracy']:
                        parameters[param_name] = float(match.group(1))
                    else:
                        parameters[param_name] = match.group(1)
                except:
                    parameters[param_name] = match.group(1)
    
    logger.info(f"   {len(parameters)} parâmetros extraídos: {list(parameters.keys())}")
    return parameters

def extract_prompts(code_cells, config):
    """Extrai prompts específicos."""
    prompts = []
    all_code = ' '.join([cell['code'] for cell in code_cells])
    
    # Detectar "prompt" ou "system_prompt"
    prompt_pattern = r'(prompt|system_prompt)\s*[:=]\s*["\'](.+?)["\']'
    matches = re.finditer(prompt_pattern, all_code, re.IGNORECASE | re.DOTALL)
    for match in matches:
        prompt_name = match.group(1)
        prompt_text = match.group(2)[:1000]
        prompts.append({
            'type': prompt_name,
            'content': prompt_text
        })
    
    logger.info(f"   {len(prompts)} prompts extraídos")
    return prompts

def save_notebook_data(notebook_data, notebook_id, html):
    """Salva metadados em JSON e HTML bruto."""
    json_path = Path(f'data_sources/raw/kaggle/aimo3_notebooks/json/{notebook_id}_metadata.json')
    html_path = Path(f'data_sources/raw/kaggle/aimo3_notebooks/html/{notebook_id}.html')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(notebook_data, f, ensure_ascii=False, indent=2)
    logger.info(f" JSON salvo: {json_path}")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    logger.info(f" HTML bruto salvo: {html_path}")

def scrape_aimo3_notebooks(config_path='data_sources/configs/aimo3_config.json', delay=3):
    """Pipeline completo de scraping dos 3 notebooks AIMO3."""
    logger.info("=" * 70)
    logger.info("INICIANDO WEB SCRAPING AIMO3")
    logger.info("=" * 70)
    
    setup_directories()
    config = load_config(config_path)
    
    results = []
    
    for notebook_config in config['notebooks']:
        logger.info(f"\n Processando: {notebook_config['title']}")
        logger.info(f"   Autor: {notebook_config['author']}")
        logger.info(f"   URL: {notebook_config['url']}")
        
        html = fetch_with_retry(
            notebook_config['url'],
            headers=get_headers(),
            timeout=config['timeouts']['request_timeout']
        )
        
        if not html:
            logger.error(f" Falha ao buscar notebook")
            results.append({
                'id': notebook_config['id'],
                'status': 'FAILED',
                'reason': 'HTTP fetch failed'
            })
            time.sleep(delay)
            continue
        
        logger.info("  Extraindo metadados...")
        metadata = parse_notebook_metadata(html, config)
        
        logger.info("  Extraindo código...")
        code_cells = extract_code_cells(html, config)
        
        logger.info("  Extraindo Markdown...")
        md_cells = extract_markdown_cells(html, config)
        
        logger.info("  Extraindo parâmetros...")
        parameters = extract_parameters(code_cells, config)
        
        logger.info("  Extraindo prompts...")
        prompts = extract_prompts(code_cells, config)
        
        notebook_data = {
            'notebook_id': notebook_config['id'],
            'metadata': {
                **metadata,
                'url': notebook_config['url'],
                'focus': notebook_config['focus'],
                'fetch_date': datetime.now().isoformat(),
                'fetch_method': 'requests_beautifulsoup'
            },
            'code_cells': code_cells,
            'markdown_cells': md_cells,
            'parameters_extracted': parameters,
            'prompts_extracted': prompts,
            'stats': {
                'code_cells_count': len(code_cells),
                'markdown_cells_count': len(md_cells),
                'parameters_count': len(parameters),
                'prompts_count': len(prompts)
            }
        }
        
        save_notebook_data(notebook_data, notebook_config['id'], html)
        
        results.append({
            'id': notebook_config['id'],
            'status': 'SUCCESS',
            'cells_code': len(code_cells),
            'parameters': len(parameters)
        })
        
        logger.info(f" Notebook processado com sucesso\n")
        time.sleep(delay)
    
    logger.info("=" * 70)
    logger.info("RESUMO DO SCRAPING")
    logger.info("=" * 70)
    for result in results:
        status_icon = "" if result['status'] == 'SUCCESS' else ""
        logger.info(f"{status_icon} {result['id']}: {result['status']}")
    
    return results

def get_headers():
    """Retorna headers para simular navegador."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8',
        'Connection': 'keep-alive'
    }

if __name__ == '__main__':
    scrape_aimo3_notebooks()
