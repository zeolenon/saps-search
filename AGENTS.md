# Orientações para agentes SAPS

1. Antes de executar, leia SKILL.md, SECURITY.md e docs/WORKFLOWS.md.
2. Confirme que a pessoa/automação possui acesso SAPS autorizado e usa credenciais próprias ou uma conta de serviço formalmente aprovada. Nunca reutilize credenciais de outro militar.
3. Use o cliente deste repositório para buscas somente leitura. O login HTTP é solicitado localmente; não leia arquivos de credenciais legados nem extraia cookies do navegador.
4. Normalize CPF/CNPJ para dígitos e deduplique antes do lote. Para edificações, faça consultas sequenciais e use timeout de leitura de até 90 s.
5. Prefira CPF/CNPJ exato. Use nome completo em maiúsculas apenas como busca candidata; uma ausência por nome não prova inexistência.
6. Não chame /serten/projetos/vistar para validar sessão. O cliente valida sessão pela resposta da própria busca e pode autenticar/repetir uma única vez se houver redirecionamento ao login.
7. Não acione links/ações na tabela nem faça vistoria, homologação ou alterações. O escopo deste repositório termina na leitura dos resultados pedidos.
8. Retorne somente os campos solicitados, contagem de linhas, resultado da comparação exata e indicador de paginação. Não alegue ausência completa se a resposta indicar próxima página.
9. Não envie credenciais, cookies, HTML integral, dados de clientes ou planilhas para repositório, issues, chat compartilhado ou logs.
