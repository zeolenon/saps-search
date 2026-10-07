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

## Integração com cliente SAPS existente

O adaptador `ExistingSessionSearch` reutiliza uma sessão já aberta do cliente
OpenClaw, sem ler arquivos de credenciais, renovar login ou persistir cookies:

    from saps_search.legacy import ExistingSessionSearch
    search = ExistingSessionSearch(cliente_saps_existente)
    result = search.search_client(cnpj="00000000000000")
    result = search.search_building(name="EMPRESA FICTICIA", city="CIDADE")

Instale o pacote no mesmo ambiente Python que executa o cliente existente.
O cliente integrado oferece os métodos `search_client` e `search_building`;
se o pacote não estiver instalado, apenas esses métodos novos falham na importação.
Listagem, monitoramento, vistoria e homologação existentes permanecem disponíveis.
O adaptador depende dos atributos privados `_client` e `_cookies` do cliente
OpenClaw e deve ser revalidado se essa interface mudar. Ele não fecha o cliente
que recebeu. Sessão ausente/expirada gera erro, sem autenticação automática.
O adaptador preserva a configuração TLS do cliente recebido; o cliente independente
usa verificação TLS. Prefira o cliente independente para novos operadores.

As latências documentadas são observações históricas de poucos testes,
não metas nem garantias. Os testes automatizados usam transporte HTTP simulado,
HTML fictício e nenhum acesso ao SAPS. Execute:

    python -m unittest discover -s tests -v

Eles verificam filtros, multiplicidade, paginação, deduplicação, timeout sem
repetição e sessão expirada sem novo login. Não validam disponibilidade,
autorização ou mudanças atuais no backend institucional.

Para incorporar os métodos ao checkout OpenClaw correspondente, revise e aplique
`integrations/openclaw-search.patch` na raiz da skill SAPS. O patch contém apenas
os dois métodos novos; não inclui o cliente legado nem suas rotinas de credenciais.
Em versões divergentes, adapte os métodos manualmente após revisar o contexto.
