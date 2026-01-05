# Runbook Operacional — Hunyuan3D-2

## Setup Inicial
- Instale dependências: `pip install -r requirements.txt`
- Configure variáveis de ambiente conforme README.md
- Execute exemplos para validação E2E

## Troubleshooting
- Erro de arquivo: verifique caminhos e permissões
- Falha de exportação: confira espaço em disco e permissões
- Dependências: reexecute instalação
- Logs: consulte arquivos em LOGDIR

## Checklist de Release/QA
- Testar fluxos API, Gradio, Blender e exemplos
- Validar estados UX (loading, error, success)
- Conferir acessibilidade mínima nos templates
- Validar logs com IDs de correlação
- Executar benchmarks de performance
- Revisar documentação e instruções

## Operação
- Monitorar logs e métricas
- Validar geração de modelos e exportação
- Revisar custos e uso de recursos

## Rollback
- Restaurar arquivos originais
- Reverter dependências
- Validar funcionamento pós-rollback

---
Este runbook deve ser revisado a cada release e expandido conforme novos fluxos e integrações.