# Política de Governança de Artefatos e Limpeza

## Objetivo
Garantir que o repositório permaneça limpo, seguro e sustentável, evitando acúmulo de arquivos desnecessários, código morto e dependências órfãs.

## Regras
- Não versionar arquivos de saída de testes, logs, modelos intermediários ou caches.
- Manter apenas artefatos de release/documentação final.
- Revisar dependências e scripts órfãos a cada release.
- Consolidar documentação para evitar redundância.
- Checklist de limpeza obrigatório antes de cada release:
  - Build/test/lint devem passar.
  - Nenhum artefato gerado deve estar versionado.
  - Scripts/tests deprecated revisados por owners.
  - Dependências revisadas.

## Processo
1. Atualizar .gitignore conforme surgirem novos artefatos.
2. Marcar scripts/tests suspeitos como deprecated antes de remover.
3. Validar toda remoção com build/test/lint.
4. Documentar rollback para cada limpeza.
5. Revisar esta política a cada 6 meses.

---

*Este arquivo deve ser revisado e atualizado por todos os owners do projeto.*
