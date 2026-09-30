# SAPS Search

Cliente Python e CLI somente leitura para pesquisar clientes e edificações no SAPS/SERTEN, usando os filtros e rotas observados.

Este projeto não lista nem vistoria processos. Não chama `/serten/projetos/vistar`, não altera registros e não salva credenciais ou cookies em disco.

## O que faz

- Busca cliente por CPF/CNPJ, nome fantasia ou protocolo REDESIM.
- Busca edificação por CPF/CNPJ ou nome fantasia e aceita os demais filtros observados no formulário.
- Envia POST direto para a rota de busca, sem carregar a página/listagem e os recursos do navegador.
- Mantém autenticação e cookies somente em memória durante a execução.
- Deduplica identificadores e serializa consultas de lotes.
- Compara documentos exatamente, após remover pontuação, e preserva todas as edificações retornadas.

A busca direta de clientes levou aproximadamente 0,5–0,9 s nos testes observados. Edificações levou cerca de 40 s até o primeiro byte da resposta, inclusive com POST direto. O POST evita o carregamento dos recursos do navegador; não elimina a demora do servidor. As buscas por nome são candidatas: o comportamento observado sugere comparação sensível a caixa/prefixo, mas isso não foi provado para todos os casos.

## Instalação local

Python 3.11 ou superior:

    git clone https://github.com/zeolenon/saps-search.git
    cd saps-search
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .

No Windows, ative o ambiente virtual com .venv\Scripts\activate.

O repositório é privado. Um administrador precisa conceder acesso GitHub individual aos militares autorizados; não compartilhe contas ou tokens.

## Login seguro

Por padrão, cada comando pede a matrícula no terminal e a senha em prompt oculto. Use a conta SAPS autorizada do próprio operador. No Brave, a extensão Bitwarden pode ajudar a localizar a entrada individual; esta CLI HTTP não lê nem reutiliza a sessão do navegador. Copie os dados localmente para os prompts, sem colá-los em mensagens, argumentos de comando, arquivos, planilhas ou logs.

Para automação não interativa, use `--env-credentials` somente com um secret manager aprovado que injete `SAPS_USERNAME` e `SAPS_PASSWORD` no processo em tempo de execução. Não crie .env, não grave credenciais em scripts nem use uma credencial pessoal compartilhada. Cada seção deve solicitar acesso autorizado para seus operadores/conta de serviço.

A senha e os cookies de sessão ficam apenas na memória do processo e são descartados ao fechar o cliente. O TLS permanece verificado.

## Busca individual

    saps-search client --cnpj 00000000000000
    saps-search client --name "NOME COMPLETO"
    saps-search client --redesim PROTOCOLO
    saps-search building --cnpj 00000000000000
    saps-search building --name "NOME COMPLETO"
    saps-search building --cnpj 00000000000000 --city "CIDADE"

O resultado é JSON no stdout. Matrícula e senha são solicitadas uma vez por execução.

Para um executor que injeta segredos por ambiente, acrescente `--env-credentials` antes do subcomando:

    saps-search --env-credentials client --cnpj 00000000000000

Nunca passe senha como argumento CLI.

## Lote de planilha/CSV

Prepare um CSV local apenas com as colunas necessárias: `target`, `cnpj_cpf` e `name`. Valores aceitos para `target`: `client`/`cliente` ou `building`/`edificacao`.

    saps-search batch examples/input-template.csv

O lote faz uma consulta por chave única, usa documento quando preenchido e nome completo em maiúsculas apenas quando não houver documento. Consultas de edificações são sequenciais; não há concorrência que sobrecarregue o SAPS. O JSON de saída preserva o número de linhas encontrado e todos os resultados de edificações. O arquivo de exemplo contém somente cabeçalho; não adicione dados reais de clientes ao repositório.

Para integrar com Google Sheets, o agente pode ler do intervalo autorizado com a ferramenta institucional já aprovada, mapear as linhas para os campos acima e consumir o JSON retornado. Este projeto não acessa nem atualiza planilhas. Faça gravações de volta como uma etapa separada, com autorização e conferência humana apropriadas.

## API Python

    from saps_search import SAPSClient, prompt_credentials

    credentials = prompt_credentials()
    with SAPSClient(credentials) as saps:
        saps.login()
        result = saps.search_client(cnpj="00000000000000")
        print(result)

Veja SKILL.md para instruções de agente e docs/ para rotas, autenticação e fluxos. Consulte SECURITY.md antes de automatizar em ambiente compartilhado.
