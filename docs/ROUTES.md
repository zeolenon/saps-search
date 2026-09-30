# Rotas e filtros observados

Origem: `https://sistemascbm.rn.gov.br`. Os dois endpoints exigem sessão SAPS autorizada. Envie os campos de formulário URL-encoded com POST direto; não carregue o GET da listagem antes da busca.

## Clientes

POST `/serten/clientes`

Campos:

- Sempre: `_method=POST`
- Sempre: `data[Filter][filterFormId]=Cliente`
- CPF/CNPJ: `data[Cliente][num_cnpj]`
- Nome fantasia: `data[Cliente][dsc_nomefantasia]`
- Protocolo REDESIM: `data[Cliente][prot_redesim]`

Foi observado que a busca pelo documento é a chave mais confiável. Testes limitados sugerem busca por nome sensível a caixa/prefixo: nome cadastrado completo em maiúsculas e seu prefixo encontraram o registro de teste; caixa mista, palavra interna e nome divergente da planilha não encontraram. Isso é uma inferência do comportamento observado, não uma especificação do backend.

Tempo observado: POST direto ~0,5–0,9 s; GET da listagem ~3 s e carregou recursos que o cliente HTTP não precisa.

## Edificações

POST `/serten/edificacoes`

Campos observados:

- Sempre: `_method=POST`
- CPF/CNPJ: `data[Edificacao][num_cnpj]`
- Nome fantasia: `data[Edificacao][dsc_nomefantasia]`
- Cliente: `data[Edificacao][cod_cliente]`
- Classificação: `data[Edificacao][cod_classificacao]`
- Endereço: `data[Edificacao][dsc_endereco]`
- UF: `data[Edificacao][dsc_uf]`
- Cidade: `data[Edificacao][dsc_cidade]`
- Bairro: `data[Edificacao][dsc_bairro]`

O formulário observado não tem `filterFormId`. Colunas do resultado: Nome Fantasia, CNPJ/CPF, Endereço, Cliente Responsável, Classificação, Sub Classificação e Ações. Uma consulta de documento retornou duas edificações com o mesmo CNPJ; preserve a multiplicidade.

Tempo observado: GET e POST levaram cerca de 40 s até a resposta. O POST direto evita recursos da página, mas não reduz o tempo gasto no backend. O cliente usa timeout de leitura de 90 s e serializa consultas.

## Login e sessão

- GET da tela de login para abrir sessão inicial, então POST para `/serten/usuarios/login` com `_method=POST`, `data[Usuario][matricula]` e `data[Usuario][senha]`.
- Não validar sessão consultando `/serten/projetos/vistar`; valide pela resposta da rota de pesquisa.
- Se a rota de pesquisa redirecionar para o login, autentique novamente e repita a mesma pesquisa uma única vez.
- Cookie jar só em memória; não exporte cookie.

Não foi mapeada a rota de detalhe/status de processo. Não adivinhe URL nem use a coluna Ações para navegar/alterar dados.
