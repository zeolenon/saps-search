# Setup e fluxos de trabalho

## Preparação individual

1. Confirme que o militar recebeu autorização própria para acessar SAPS e ao repositório privado.
2. Instale Python 3.11+ e clone o repositório.
3. Crie e ative um ambiente virtual; instale o projeto com python -m pip install -e ..
4. Execute uma consulta pontual. No primeiro uso, informe matrícula e senha nos prompts; a senha não aparece na tela e não é armazenada.
5. Confirme que a resposta é JSON e contém a rota, o resultado da comparação e a contagem. Nunca cole credenciais ou dados reais em arquivos do repositório.

## Bitwarden

A extensão do Brave preenche o formulário SAPS no navegador, mas não injeta a sessão ou credenciais na CLI HTTP. Para a CLI, localize no próprio vault do operador a entrada individual do domínio SAPS e cole o usuário no prompt e a senha no prompt oculto. Não use conta de colega e não envie conteúdo do vault ao agente.

Para execução não interativa, obtenha aprovação do administrador e use conta de serviço autorizada. Injete os dois valores no ambiente pelo secret manager institucional e execute com `--env-credentials`; não grave esses valores em arquivo, variável permanente do shell, configuração de cron ou workflow versionado.

## Pesquisa por planilha

1. Leia somente as colunas necessárias com o conector autorizado: `target`, `cnpj_cpf`, `name`.
2. Normalize documentos para dígitos e deduplique; o lote faz cache da chave na própria execução.
3. Se houver CPF/CNPJ, use-o. Sem documento, use o nome completo em maiúsculas uma única vez.
4. Rode o lote sequencialmente. Edificações podem levar cerca de 40 s por chave; não paralelize.
5. Confira `outcome`, `returned_rows`, `has_next_page` e todos os `matches`. Se houver paginação, não conclua ausência definitiva.
6. Mapeie JSON de volta às linhas da planilha. Atualizar a planilha é uma operação separada; não grave sem autorização específica e conferência do destino.

CSV mínimo:

    target,cnpj_cpf,name
    client,,
    building,,

O arquivo `examples/input-template.csv` contém somente esse cabeçalho.

## Integração Python

    from saps_search import SAPSClient, prompt_credentials
    from saps_search.batch import search_rows

    rows = [
        {"target": "client", "cnpj_cpf": "00000000000000", "name": ""},
        {"target": "building", "cnpj_cpf": "00000000000000", "name": ""},
    ]
    with SAPSClient(prompt_credentials()) as saps:
        saps.login()
        results = search_rows(saps, rows)

Passe objetos obtidos de conectores autorizados. Não registre linhas, credenciais, cookie, HTML bruto ou resposta integral em logs compartilhados.
