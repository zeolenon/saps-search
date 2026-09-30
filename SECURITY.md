# Segurança e credenciais

## Regras obrigatórias

- Use somente conta SAPS individual ou conta de serviço formalmente autorizada para a seção.
- Não reutilize nem distribua a credencial pessoal de outro militar.
- Não inclua matrícula, senha, token, cookie, planilha real, CPF/CNPJ de pessoa/empresa ou resposta real em commits, issues, exemplos, logs ou prompts.
- Não passe senha em argumento de comando: argumentos podem aparecer no histórico e na lista de processos.
- Não desative verificação TLS. Se houver erro de certificado, use apenas CA aprovada pelo ambiente.
- Mantenha a sessão em memória e finalize o processo após o lote.
- Trate resultados SAPS e planilhas com os controles de acesso institucionais existentes.

## Entrada de credenciais

O modo interativo solicita a matrícula e usa getpass para que a senha não apareça na tela. O Bitwarden pode ser usado localmente para consultar a entrada individual; a CLI não acessa o navegador nem importa cookies da extensão.

Para um fluxo automatizado, `--env-credentials` lê `SAPS_USERNAME` e `SAPS_PASSWORD` do ambiente do processo. Injete-os por um gerenciador de segredos aprovado imediatamente antes da execução; não os armazene em .env, arquivos de configuração, cron, YAML de workflow ou logs. Prefira uma conta de serviço autorizada, com escopo e rotação definidos pelo administrador.

A senha não é salva em disco. Cookies de sessão são mantidos no cookie jar httpx em memória, não são exportados e não são reutilizados após o processo. Não há telemetria nem logging de corpo de requisição/resposta.

## Escopo

O cliente faz apenas POSTs de pesquisa nas rotas de clientes e edificações. Não chama vistoria, homologação, exclusão, edição ou qualquer ação. Não use para contornar autenticação ou autorização do SAPS.
