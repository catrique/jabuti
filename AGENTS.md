# Diretrizes para agentes

Este arquivo orienta agentes de código que trabalham no repositório Jabuti.

## Princípios de desenvolvimento

- Preserve a arquitetura existente e mantenha o projeto pequeno.
- Não crie abstrações sem uma necessidade real e atual.
- Mantenha responsabilidades bem separadas e o acoplamento baixo.
- Evite funções e arquivos excessivamente grandes.
- Favoreça código legível, explícito e com nomes descritivos.
- Evite dependências sem uma justificativa clara.
- Detecte ferramentas do sistema; não tente instalá-las ou alterar o ambiente.
- Execute subprocessos com argumentos separados e sem shell quando não houver
  necessidade real.
- Dependências do projeto podem ser instaladas dentro do próprio projeto.
- Escreva ou atualize testes sempre que um comportamento for alterado.
- Priorize testes de comportamentos críticos e evite testes de baixo valor.
- Execute os testes e o lint antes de considerar uma tarefa concluída.
- Verifique a segurança das alterações e nunca inclua secrets, credenciais ou
  dados específicos da máquina local.
- Não faça alterações fora do escopo solicitado.
- Nunca execute `git push` automaticamente.

## Regras permanentes do Jabuti

- Templates são recursos do pacote (`src/jabuti/templates/`), lidos com
  `importlib.resources`; nunca dependa de caminhos do repositório.
- O planner é a fonte de verdade dos diretórios de cada componente.
- O Jabuti não gera arquivos de deploy, workflows de deploy/migrations nem
  qualquer configuração de servidor ou infraestrutura.
- O Jabuti nunca gera credenciais nem cria `.env` real.
- Migrations são apenas locais (Alembic) e nunca executam automaticamente.
- Subprocessos usam lista de argumentos, sem shell e sem `os.system`.
- Testes focam comportamentos críticos; evite testes de baixo valor.

## Fluxo de trabalho com Git

Depois de concluir uma tarefa solicitada:

1. Revise todas as alterações.
2. Execute os testes.
3. Execute o lint.
4. Verifique o `git diff`.
5. Crie um commit claro e objetivo.
6. Nunca execute `git push` automaticamente.
