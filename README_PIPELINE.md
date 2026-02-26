# AIMO Prize 3: Sequential Pipeline Guide

## ✓ Status: Implementation Complete

- ✅ Notebook criado: `notebooks/AIMO3_Experiment1_Sequential.ipynb`
- ✅ Dryrun validado (100% pass@1 em modo mock)
- ✅ Verifier implementado (format, bounds, heurísticos)
- ✅ Runner configurado (dryrun + real modes)
- ✅ Análise + Decision Gate completa

---

## 🚀 Quick Start

### 1. **Validar Dados**
```bash
python scripts/validate_data.py
```
Resultado esperado: 13 problemas (10 reference + 3 test), intervalo [0, 99999] ✓

### 2. **Abrir Notebook Sequential**
```
notebooks/AIMO3_Experiment1_Sequential.ipynb
```

### 3. **Executar Células em Sequência**

| Célula | Nome | Função | Estimado |
|--------|------|--------|----------|
| 1 | Setup | Setup e paths | < 1s |
| 2 | Load Data | Carrega CSV | < 1s |
| 3 | Verifier | Setup verificador | < 1s |
| 4 | Runner | Define classe Runner | < 1s |
| 5 | Dryrun | Mock test (3 problemas) | 1–5s |
| 6 | Experiment 1 | Full baseline (13 problemas) | **2–4h H100** |
| 7 | Analysis | Análise problema-por-problema | < 1s |
| 8 | Decision Gate | Decision + recomendações | < 1s |

### 4. **Decision Gate Outputs**

Após Experiment 1, o notebook genera:

- **Métrica**: pass@1, pass@3, format_fail_rate
- **Decision**: 
  - `SUBMIT_OR_OPTIONAL_ENSEMBLE` (se pass@1 ≥ 60%)
  - `EXECUTE_EXPERIMENT_2` (se pass@1 < 60% mas pass@3 ≥ 60%)
  - `STOP_REWORK_PROMPTS` (se format_fail_rate > 30%)
  - `EVALUATE_SFT` (borderline case)

---

## 📊 Estimativas vs Realidade

### Esperado (Baseline - Experiment 1)
| Métrica | Min | Max |
|---------|-----|-----|
| pass@1 | 30% | 55% |
| pass@3 | 45% | 70% |
| format_fail_rate | 10% | 30% |

### Observado (Dryrun Mock)
| Métrica | Value |
|---------|-------|
| pass@1 | 100% |
| pass@3 | 100% |
| format_fail_rate | 0% |

**Nota**: Dryrun usa respostas corretas (mock). Resultados reais em H100 serão menores.

---

## 🔧 Para Rodar em H100 Real

### Passo 1: Modificar Runner para vLLM

Em `notebooks/AIMO3_Experiment1_Sequential.ipynb`, Célula 4 (Runner):

Adicionar após `import` section:
```python
# TODO: Integrate vLLM
from vllm import LLM, SamplingParams

llm = LLM(
    model="deepseek-math-7b-rl",  # ou outro modelo
    tensor_parallel_size=1,
    trust_remote_code=True
)
```

Modificar método `call_model()`:
```python
def call_model(self, prompt, problem_id, temp=0.0, max_tokens=256):
    params = SamplingParams(temperature=temp, max_tokens=max_tokens)
    output = llm.generate(prompt, params)
    return output[0].outputs[0].text
```

### Passo 2: Mudar para Modo 'run'

Célula 6:
```python
experiment_runner = Runner(mode='run', seed=42)  # Mude de 'dryrun'
```

### Passo 3: Executar

Pronto! As células 6–8 rodarão em H100 com respostas reais do modelo.

---

## 📁 Arquivos Gerados

Após rodar o notebook:

```
results/
├── dryrun_responses.jsonl       # Responses do dryrun
├── dryrun_results.csv            # Sumarizado (dryrun)
├── exp1_baseline_responses.jsonl # Responses full (Exp1)
└── exp1_baseline_results.csv     # Sumarizado (Exp1)

reports/
└── exp1_decision.md              # Decision report
```

### Formato JSONL (responses)
```json
{
  "id": "0e644e",
  "problem": "Let ABC be...",
  "prompt_type": "direct",
  "raw_response": "336",
  "parsed_answer": 336,
  "verification_passed": true,
  "verification_checks": {"format": true, "bounds": true, "parity": true},
  "time_s": 2.5,
  "expected_answer": 336,
  "correct": true
}
```

### Formato CSV (results)
```csv
id,prompt_type,parsed_answer,verified,expected,correct,time_s
0e644e,direct,336,True,336,True,2.50
```

---

## 🔀 Próximos Passos (Experiment 2)

Se Decision = `EXECUTE_EXPERIMENT_2`:

1. Criar `notebooks/AIMO3_Experiment2_Ensemble.ipynb`
2. Configurar 3 prompts: `['direct', 'cot_short', 'decompose']`
3. Rodar 3 samples por prompt per problem
4. Reranking por majority vote + verificador
5. Medir ganho: esperado +5–12 pp em pass@1
6. Budget: 6–8h H100

---

## 🛠️ Troubleshooting

### Format Failure Rate > 30%?
- [ ] Rever prompts em `prompts/strategies/`
- [ ] Reduzir temperature para 0.0
- [ ] Adicionar instruções mais explícitas ("Answer ONLY with...")
- [ ] Implementar re-call lógica (2–3 tentativas)

### CAS Errors > 40%?
- [ ] Limitar CAS a problemas com expressões simbólicas detectadas
- [ ] Marcar casos para revisão humana
- [ ] Usar apenas heurísticas para problemas simples

### H100 Timeout?
- [ ] Aumentar `timeout_per_call` em config
- [ ] Reduzir `max_tokens` se possível
- [ ] Implementar batch processing com vLLM

---

## 📝 Anotações

- **Reprodutibilidade**: Seed 42 fixo em todas as células
- **Logging**: Estruturado em JSONL para auditoria
- **Versioning**: Prompts versionados via git commits
- **Compliance**: Dados validados contra intervalo [0, 99999]

---

## 🎯 Meta Final

**Objetivo**: 40–60% pass@1 após Exp1+Exp2 (condicional)
**Prazo**: 2–8h H100 (Exp1 obrigatório, Exp2 condicional)
**Saída**: `sample_submission.csv` compatível com Kaggle + relatório final

---

Boa sorte na competição! 🚀
