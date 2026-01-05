# Checklist de Benchmarks e Performance — Hunyuan3D-2

## Benchmarks
- Medir tempo de execução dos principais pipelines (API, Gradio, exemplos)
- Medir uso de memória durante geração e exportação
- Validar uso de CPU/GPU (offload, paralelismo)
- Registrar logs de performance com IDs de correlação

## Instrumentação
- Adicionar timers nos pontos críticos dos pipelines
- Registrar métricas em logs estruturados
- Comparar resultados antes/depois de otimizações

## Validação
- Executar benchmarks em ambiente de teste
- Analisar logs e métricas
- Documentar resultados e ações tomadas

---
Checklist deve ser revisado a cada ciclo de otimização ou release.