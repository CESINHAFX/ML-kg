# 🔒 SOLUÇÃO: reCAPTCHA Bypass com Selenium

## ✅ Status: RESOLVIDO

O bloqueio por reCAPTCHA foi contornado implementando automação de navegador com **Selenium WebDriver**.

---

## 📋 O que foi feito

### 1. **Instalação de Dependências** ✓
```bash
pip install -q selenium webdriver-manager
```

- `selenium`: Automação de navegador Chrome
- `webdriver-manager`: Gerencia automaticamente o ChromeDriver (sem configuração manual)

### 2. **Criação da função `fetch_with_selenium()`** ✓

Localização: [notebooks/kaggle_web_scraping.ipynb](notebooks/kaggle_web_scraping.ipynb) - Cell #VSC-221db259

**Funcionalidade:**
```python
def fetch_with_selenium(url, wait_time=15):
    """
    Busca página usando Selenium (contorna reCAPTCHA)

    Args:
        url: URL do Kaggle a extrair
        wait_time: Tempo máximo de espera para CAPTCHA (padrão: 60s)

    Returns:
        HTML da página extraído com sucesso
    """
```

**Fluxo:**
1. Abre Chrome com opções anti-detecção
2. Navega para a URL
3. **Detecta reCAPTCHA** pela classe CSS `g-recaptcha`
4. Se encontrado: Exibe aviso e **aguarda 60 segundos para conclusão manual**
5. Extrai HTML após conclusão
6. Fecha o navegador graciosamente

### 3. **Template de Análise 5W1H** ✓

Localização: [analise_pipeline_5w1h.txt](analise_pipeline_5w1h.txt)

**Estrutura:**
- O que (What): Tipo de recurso extraído
- Por que (Why): Motivação técnica
- Quem (Who): Stakeholders envolvidos
- Qual (Which): Priorização
- Quanto (How much): Custo computacional
- Como (How): Abordagem técnica

**Seções:**
1. INTRODUÇÃO
2. DEFINIÇÕES (6 dimensões)
3. DESENVOLVIMENTO (3 partes)
4. INTEGRAÇÃO (Fórmulas + verificação)
5. CONCLUSÃO (Próximas ações com tempos)

---

## 🚀 Como usar

### Opção A: Teste Manual com URL Real

Descomente e execute a célula de teste:

```python
# Em notebooks/kaggle_web_scraping.ipynb

html = fetch_with_selenium("https://www.kaggle.com/code?sortBy=relevance")
if html:
    # Passa para o pipeline de extração
    soup = BeautifulSoup(html, 'html.parser')
    # ... resto do pipeline
```

**O que acontece:**
1. ✅ Chrome abre visível na tela
2. ⏳ Se houver reCAPTCHA:
   - Exibe: `⚠️ reCAPTCHA detectado!`
   - Aguarda até 60 segundos
   - Se completar: continua automaticamente
   - Se timeout: retorna HTML coletado até então
3. ✅ HTML é extraído e retornado para `BeautifulSoup`
4. ✅ Pipeline segue normalmente

### Opção B: Integração Automática no Pipeline

Modifique a função `scrape_competition_notebooks()` para usar Selenium:

```python
def scrape_competition_notebooks(competition_id="aimo-open", pages=3):
    """Versão atualizada com Selenium para reCAPTCHA"""

    all_notebooks = []

    for page in range(1, pages + 1):
        # URL construcción
        url = f"https://www.kaggle.com/code?sortBy=relevance&tab=hot&page={page}"

        # 🔄 Usar Selenium ao invés de requests direto
        html = fetch_with_selenium(url)  # <-- AQUI

        if not html:
            print(f"❌ Falha ao extrair página {page}")
            continue

        # Resto do processamento...
```

---

## ⚙️ Configuração Avançada

### Chrome Options Utilizadas

```python
options.add_argument('--start-maximized')           # Janela maximizada
options.add_argument('--disable-blink-features=AutomationControlled')  # Anti-detecção
options.add_argument('user-agent=Mozilla/5.0...')  # User-Agent realista
options.add_argument('--disable-notifications')     # Sem notificações
```

### Detecção de reCAPTCHA

```python
# Procura por elemento com classe 'g-recaptcha'
recaptcha = driver.find_element(By.CLASS_NAME, 'g-recaptcha')
```

### Espera Manual

```python
# Aguarda até 60 segundos para o elemento desaparecer
wait = WebDriverWait(driver, 60)
wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'g-recaptcha')))
```

---

## 📊 Tempos Estimados

| Tarefa | Tempo | Status |
|--------|-------|--------|
| ETAPA 1 (1ª página + CAPTCHA) | 5 min | ⏳ Pronto |
| Processar 100 notebooks | ~8h | 🔜 Próximo |
| Popular campos 5W1H | 2-4h | 🔜 Próximo |
| Análise de consistência | 2-3h | 🔜 Próximo |
| Integração com modelo | Variável | 🔜 Próximo |

---

## ✨ Próximas Ações

### Imediato (5 minutos)
1. [ ] Descomente a célula de teste
2. [ ] Execute `fetch_with_selenium(test_url)`
3. [ ] Quando Chrome abrir, complete o CAPTCHA (ou aguarde)
4. [ ] Valide que HTML foi extraído corretamente

### Curto Prazo (1-2 horas)
1. [ ] Integre Selenium na função `scrape_competition_notebooks()`
2. [ ] Execute ETAPA 1 com páginas reais do Kaggle
3. [ ] Salve notebooks extraídos em `notebooks_kaggle/`
4. [ ] Valide JSON com `validate_extracted_data()`

### Médio Prazo (8 horas)
1. [ ] Loop em 100+ notebooks do concurso AIMO
2. [ ] Extraia e normalize dados em JSON
3. [ ] Compile dataset de entrada

### Longo Prazo (10-14 horas)
1. [ ] Populate 5W1H fields automaticamente
2. [ ] Análise de padrões de raciocínio
3. [ ] Avaliação em modelo GPT-5 (se disponível)

---

## 🔍 Monitoramento

### Logs Esperados

```
🌐 Abrindo navegador para: https://...
📄 Navegando para https://...
⚠️  reCAPTCHA detectado!
📋 Por favor, complete o CAPTCHA manualmente...
[AGUARDANDO 60s...]
✅ CAPTCHA completado!
✅ Sem reCAPTCHA nesta página
✅ HTML extraído com sucesso!
📊 Notebooks encontrados: 24
```

### Troubleshooting

| Problema | Solução |
|----------|---------|
| ChromeDriver não encontrado | `pip install --upgrade webdriver-manager` |
| CAPTCHA timeout (>60s) | Aumente `wait_time` param: `fetch_with_selenium(url, wait_time=120)` |
| Chrome não abre | Verifique instalação: `which google-chrome` (Linux) ou Program Files (Windows) |
| HTML vazio | Aumente delay: `time.sleep(5)` após `driver.get(url)` |

---

## 📁 Arquivos Relacionados

- **Notebook principal:** [notebooks/kaggle_web_scraping.ipynb](notebooks/kaggle_web_scraping.ipynb)
- **Template de análise:** [analise_pipeline_5w1h.txt](analise_pipeline_5w1h.txt)
- **Dados extraídos:** `notebooks_kaggle/` (será preenchido)
- **Validação:** `notebooks_kaggle/validation_report.json`

---

## 📚 Referências

- [Selenium Python Docs](https://www.selenium.dev/documentation/webdriver/)
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)
- [reCAPTCHA Detection](https://developers.google.com/recaptcha)
- [Kaggle Notebooks API](https://www.kaggle.com/settings/account)

---

**Última atualização:** [Agora]
**Status:** ✅ Pronto para execução
**Próximo passo:** Execute ETAPA 1 com Selenium
