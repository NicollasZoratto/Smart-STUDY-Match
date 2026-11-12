// P2 — Relatório consolidado (ISW055) — Nicollas Zoratto de Carvalho
#let aluno = "Nicollas Zoratto de Carvalho"
#let produto = "StudyMatch"
#let repo = "https://github.com/NicollasZoratto/Smart-STUDY-Match"
#let dominio = "https://nicollas-carvalho-isw055.lapps.studio"

#set document(title: "P2 — Relatório consolidado", author: aluno)
#set text(lang: "pt", region: "br", size: 11pt)
#set par(justify: true, leading: 0.62em)
#show link: set text(fill: rgb("#b5651d"))
#show raw: set text(size: 9pt)
#set table(stroke: 0.5pt + luma(150), inset: 5pt)
#show figure.caption: set text(size: 8.5pt, fill: luma(90))
#show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em, it)
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.6em, it)

#let cab(..args) = table.cell(fill: luma(235), strong(..args))
#let fig(arquivo, legenda, w: 100%) = figure(image("prints/" + arquivo, width: w), caption: legenda)

// ---------- dados das atividades (o quadro e as fichas leem daqui) ----------
#let atividades = (
  (n: 7, titulo: "Plano Premium — cobrança de verdade com Stripe",
   desc: "Plano pago em modo de teste: Checkout Session do Stripe e webhook marcando o usuário como premium.",
   plan: "09/10/2026", real: "08/10/2026 19:35", sit: "entregue",
   evid: "GitHub — commit + print do checkout concluído e do usuário premium",
   url: repo + "/commit/94dd5c7e09c3723628669314fa9a4be35d176c96"),
  (n: 8, titulo: "SaaS, PaaS, IaaS — e a documentação que o projeto nunca teve",
   desc: "Camadas de nuvem do próprio projeto e documentação reversa: especificação, arquitetura, regras de negócio e modelo de dados.",
   plan: "16/10/2026", real: "21/10/2026 19:47", sit: "entregue com atraso",
   evid: "GitHub — commit + documentação linkada no README",
   url: repo + "/commit/cdb7a74e446c980b4e6171ed7e4ad77c4f0e2c98"),
  (n: 9, titulo: "Fork e plano de negócio",
   desc: "Repositório novo com o histórico do anterior, README do produto (dor, persona, Lean Canvas, modelo de receita, mapa de reaproveitamento) e backlog em issues.",
   plan: "23/10/2026", real: "21/10/2026 20:10", sit: "entregue",
   evid: "GitHub — issue de entrega (\@siriani) + repositório novo + README do produto + prints do histórico e das issues",
   url: repo + "/issues/9"),
  (n: 10, titulo: "Seu negócio no ar — o domínio no lugar dos filmes",
   desc: "Stack apontando para o repositório novo, tabelas e API do domínio, papéis do negócio, isolamento por usuário, eventos no log, upload e landing page.",
   plan: "06/11/2026", real: "09/11/2026 19:33", sit: "entregue com atraso",
   evid: "GitHub — issue de entrega (\@siriani) + commit + URL no ar + prints da landing, do 403 e dos eventos no log",
   url: repo + "/issues/10"),
  (n: 11, titulo: "SaaS completo — planos, limites e assinatura com Stripe",
   desc: "Planos recorrentes, checkout de assinatura, webhooks atualizando o plano, portal do cliente, limites por plano na API e painel admin.",
   plan: "13/11/2026", real: "11/11/2026 19:51", sit: "entregue",
   evid: "GitHub — issue de entrega (\@siriani) + commit + prints da assinatura com o cartão 4242, do Stripe em modo de teste, do webhook e do limite bloqueando",
   url: repo + "/issues/11"),
)

// ---------- capa ----------
#page(numbering: none, header: none, footer: none)[
  #set align(center)
  #v(3.2cm)
  #text(size: 11pt, tracking: 2pt)[FATEC POMPEIA]
  #v(0.4cm)
  #text(size: 9.5pt, fill: luma(100))[Introdução à Computação em Nuvem · ISW055 · 161_SIST. INTELIGENTES_N]
  #v(4.2cm)
  #text(size: 26pt, weight: "bold")[P2]
  #v(0.9cm)
  #text(size: 17pt, weight: "bold")[Relatório consolidado]
  #v(0.5cm)
  #text(size: 12pt)[arquitetura e atividades do 2º bimestre]
  #v(0.6cm)
  #text(size: 10pt, fill: luma(100))[Avaliação individual · 2026.2]
  #v(3.6cm)
  #text(size: 13pt)[#aluno]
  #v(0.4cm)
  Produto: *#produto*\
  #text(size: 9.5pt)[#link(repo)]
  #v(1fr)
  #text(size: 10pt)[Prof. Allan Lincoln Rodrigues Siriani\
  Pompeia, 12/11/2026]
]

#set page(
  paper: "a4", margin: (x: 2.3cm, top: 2.6cm, bottom: 2.4cm),
  header: [
    #set text(size: 8pt, fill: luma(110))
    ISW055 · P2 — Relatório consolidado #h(1fr) #aluno
    #v(-0.55em) #line(length: 100%, stroke: 0.4pt + luma(190))
  ],
  numbering: "1",
)
#counter(page).update(1)
#set heading(numbering: "1.1")
#outline(title: [Sumário], depth: 3, indent: auto)
#pagebreak()

= Introdução

A disciplina Introdução à Computação em Nuvem (ISW055), da Fatec Pompeia, propõe que o aluno construa, ao longo do semestre, um sistema web completo e o coloque no ar usando os serviços típicos da nuvem: containers orquestrados pelo Portainer, banco de dados gerenciado, armazenamento de objetos, fila de eventos, autenticação por microsserviço e cobrança por assinatura. No primeiro bimestre o sistema foi um catálogo de filmes do Tom Hanks; neste segundo bimestre ele deixou de servir a um catálogo e passou a servir a um negócio.

O negócio escolhido foi o *#produto*: uma plataforma que une estudantes em grupos de estudo por disciplina e horário, pensada para quem trabalha de dia e estuda à noite. A dor que ele resolve é a dificuldade de achar colegas da mesma matéria com horário em comum, hoje improvisada em grupos de WhatsApp que esfriam em poucas semanas. O repositório foi copiado com todo o histórico para um repositório novo e passou a ter papéis do negócio (administrador, líder de grupo e estudante), API própria, limites por plano e assinatura recorrente no Stripe, em modo de teste.

Este relatório tem duas metades. A primeira (seção 3) descreve a arquitetura do sistema *que está no ar*, não um projeto ideal: componentes, onde roda, o caminho de uma requisição, o ciclo de vida de uma assinatura, o modelo de dados, a segurança e as camadas IaaS, PaaS e SaaS. A segunda (seções 4 e 5) é o quadro das atividades 7 a 11, com data planejada, data realizada e uma ficha com a evidência de cada entrega, inclusive as que saíram com atraso.

= Metodologia

As atividades 7 e 8 foram feitas no repositório público do catálogo de filmes (NicoFlix), o mesmo do primeiro bimestre. Na atividade 9 esse repositório foi copiado, com todos os commits, para um repositório novo com o nome do produto, onde o SaaS foi desenvolvido nas atividades 10 e 11, na mesma stack do Portainer e no mesmo domínio. Como o histórico foi copiado inteiro, os commits das atividades 7 e 8 têm o mesmo hash nos dois repositórios, e os links deste relatório apontam para o repositório novo.

As datas e horas de cada entrega vêm do histórico do Git (`git log`, no fuso de Brasília), conferidas na página do commit no GitHub e, da atividade 9 em diante, na issue de entrega que menciona o professor, cuja data de abertura também vale como evidência. As atividades 7 e 8 usam o horário do commit; as atividades 9, 10 e 11 usam o horário da issue de entrega. Os prints mostram a página do commit ou da issue com a data visível e o resultado do sistema em execução. Dados pessoais (e-mail e nome do titular nos prints do Stripe) foram borrados.

O código e a documentação foram escritos com o apoio do assistente de IA Claude (Anthropic), usado como ferramenta de programação e redação; as decisões, a configuração do Portainer, do Stripe e do GitHub e os testes no sistema no ar foram feitos por mim. O sistema tem testes automatizados com pytest (61 testes na última entrega), que rodam sem banco nem Stripe reais, e a verificação final foi manual, no domínio publicado.

= Arquitetura do SaaS

== Visão geral e componentes

O sistema é composto por três serviços Flask (app, auth-service e log-service), um Redis, um MinIO e um banco MariaDB externo, além do Stripe, do Mailtrap e do GitHub como serviços de terceiros. Só o app é público pelo domínio; o auth-service, o log-service e o Redis existem apenas na rede interna do Docker. A API do MinIO tem uma porta publicada porque o navegador baixa as imagens direto dele, por URL pré-assinada e temporária. O Stripe fala com o app por webhook assinado.

#fig("d1.png", [Diagrama de componentes e microsserviços do SaaS.])

#table(columns: (2.5cm, 1fr, 3.3cm, 3.3cm),
  cab[Componente], cab[Responsabilidade], cab[Tecnologia / imagem], cab[Público?],
  [app (`web`)], [telas, API REST de grupos, landing page, checkout, portal e webhook do Stripe, painel admin], [Flask, Python 3.10], [sim (domínio)],
  [auth-service], [cadastro, login com 2FA, JWT, papéis, redefinição de senha por e-mail], [Flask, JWT HS256], [não (interno, :5001)],
  [log-service], [recebe e lista eventos de negócio e auditoria], [Flask], [não (interno, :5002)],
  [Redis], [armazenamento dos logs (Redis Stream, até 10.000 eventos)], [redis:7-alpine], [não (interno)],
  [MariaDB], [usuários, grupos, disciplinas, perfis, assinaturas], [MariaDB externo da disciplina], [não (acesso por credencial)],
  [MinIO], [fotos de perfil e capas dos grupos], [bitnamilegacy/minio], [só a API (:29517), via URL assinada],
  [Stripe (externo)], [checkout, assinaturas, portal, webhooks], [serviço SaaS], [webhook → app],
)

== Onde roda

O sistema roda em uma única stack do Portainer (stack `smartstudymatch`), na mesma VM e no mesmo domínio usados desde o começo do semestre: #link(dominio). A stack puxa o código do repositório novo (#link(repo), branch `main`) e o Portainer faz o build das imagens a cada _Pull and redeploy_. São cinco containers (`nicoflix_web`, `nicoflix_auth`, `nicoflix_logs`, `nicoflix_redis` e `nicoflix_minio`; os nomes dos containers foram mantidos do projeto anterior) em uma rede interna `nicoflix-net`, mais o volume `minio_data` para os arquivos. O limite de memória por container é o do enunciado (1 GB), aplicado pela infraestrutura, e não configurado no `docker-compose.yml`.

As configurações sensíveis entram por variáveis de ambiente da stack. Os nomes são: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET`, `SECRET_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`, `GRUPOS_LIMITE_GRATIS`, `MINIO_ROOT_USER` e `MINIO_ROOT_PASSWORD`. O arquivo `.env.example` do repositório traz só os nomes.

== Fluxo de uma requisição

Exemplo: um líder de grupo cria um novo grupo de estudo.

+ O navegador envia `POST /grupos/novo` ao domínio, por HTTPS, com o cookie de sessão do Flask, que guarda o JWT do usuário.
+ O app chama o auth-service (`/validate-token`) para validar o JWT; o auth-service devolve `user_id`, nome e papel. Sem token válido, o usuário é redirecionado ao login.
+ O app confere o papel: `admin` e `lider` podem criar; `estudante` recebe 403 (e o acesso negado é registrado no log).
+ Se o usuário não é Pro, o app conta no MariaDB os grupos que ele criou no mês; no 4º, responde 403 com a mensagem do limite do plano Free.
+ O app valida os campos (título, disciplina existente, horários, vagas) e faz o `INSERT` em `grupos`, com `lider_id` igual ao id do JWT, nunca ao de um campo do formulário.
+ O app envia o evento `grupo_criado` ao log-service, que o grava no Redis Stream, e responde com redirecionamento para a página do grupo.

== Fluxo de assinatura

O usuário Free clica em _Assinar Pro_ (`POST /assinar`). O app cria, se ainda não existir, um Customer no Stripe, guarda o id dele em `assinaturas` e cria uma Checkout Session com `mode=subscription`, levando o id do usuário em `client_reference_id`. O pagamento acontece na tela hospedada pelo Stripe, então nenhum dado de cartão passa pelo servidor nem pelo banco. Ao voltar para o app, o plano só muda quando o webhook chega: a página de sucesso apenas informa.

O endpoint `POST /stripe/webhook` valida a assinatura do cabeçalho `Stripe-Signature` com o segredo do webhook (requisições sem assinatura válida recebem 400 e nada é gravado) e trata quatro eventos: `checkout.session.completed` (guarda customer e subscription e põe o plano em Pro), `customer.subscription.updated` (atualiza status, preço e cancelamento agendado), `customer.subscription.deleted` (volta o usuário ao Free) e `invoice.payment_failed` (marca `past_due` e tira o Pro). Cada `event.id` é gravado em `stripe_eventos` com `INSERT IGNORE`; se o mesmo evento chegar de novo, o app responde 200 e não processa de novo, então o resultado não muda. Se o processamento falha, a marca é desfeita e a resposta é 500, para o Stripe reenviar. O cancelamento é feito pelo portal do cliente (_Gerenciar assinatura_, `POST /assinatura/portal`), que gera `customer.subscription.updated` e `customer.subscription.deleted`. Como toda rota que depende do plano lê o banco a cada requisição, o limite do Free vale na API e não apenas na tela.

#fig("d2.png", [Fluxo de assinatura: checkout → webhook → plano no banco → limites.])

== Modelo de dados do domínio

As tabelas do negócio são `disciplinas`, `grupos` e `grupo_membros`, criadas pelo script versionado `db/001_dominio.sql`, que o app executa ao iniciar (com a seed das disciplinas); `db/002_assinaturas.sql` cria `stripe_eventos`. As chaves estrangeiras reais são `grupos.disciplina_id` → `disciplinas`, `grupo_membros.grupo_id` → `grupos` (com `ON DELETE CASCADE`) e `reset_tokens.usuario_id` → `usuarios`. A ligação com o usuário (`grupos.lider_id`, `grupo_membros.user_id`, `perfis.user_id` e `assinaturas.user_id`) é lógica, e não uma chave estrangeira, porque a tabela `usuarios` pertence a outro serviço (o auth-service). A tabela `assinaturas` liga o usuário ao plano e aos identificadores do Stripe (`stripe_customer_id`, `stripe_subscription_id`, `stripe_price_id`).

#fig("d3.png", [Modelo de dados do domínio (linhas contínuas: chaves estrangeiras; tracejadas: referências lógicas por `user_id`).])

== Segurança

#table(columns: (1fr, auto, auto, auto),
  cab[Ação], cab[admin], cab[líder], cab[estudante],
  [criar grupo], [sim], [sim (Free: 3 por mês)], [não (403)],
  [editar, excluir e enviar capa do próprio grupo], [sim], [sim], [não (403)],
  [ver o grupo de outro usuário], [sim], [não (403)], [só se for membro],
  [editar ou excluir grupo de outro usuário], [sim], [não (403)], [não (403)],
  [ver `/admin/logs` e `/admin/painel`], [sim], [não (403)], [não (403)],
  [assinar o Pro e abrir o portal do cliente], [sim], [sim], [sim],
)

As permissões valem no backend, e não só na tela: uma chamada direta à API com papel sem permissão recebe 403. O isolamento por usuário é garantido nas consultas e nas funções de acesso: o líder só lista os grupos em que `lider_id` é o seu, o estudante só os de que é membro, e abrir ou alterar o grupo de outra pessoa responde 403 e gera um evento no log. O id do usuário sempre vem do JWT validado pelo auth-service, nunca de campos enviados pelo cliente.

Os segredos do Stripe (`STRIPE_SECRET_KEY` e `STRIPE_WEBHOOK_SECRET`) ficam só nas variáveis de ambiente da stack, e o repositório tem apenas o `.env.example` com os nomes. Há limitações que reconheço: o `docker-compose.yml` ainda traz valores padrão de desenvolvimento para as credenciais do banco, o `JWT_SECRET` e o MinIO, que deveriam ser removidos; e as senhas dos usuários ainda são gravadas em texto puro em `usuarios.password` (o certo seria guardar um hash). Ambas estão registradas como pendências.

== Observabilidade, CI/CD e documentação da API

Não implementei as atividades extras de health checks e métricas, pipeline do GitHub Actions ou Swagger. O que existe: os eventos de negócio e de auditoria no log-service (visíveis ao admin em `/admin/logs`), o painel `/admin/painel` com usuários por plano, assinaturas ativas, MRR de teste e últimos eventos, 61 testes automatizados com pytest e a API REST documentada no README do repositório.

== Camadas IaaS, PaaS e SaaS do projeto

#table(columns: (2.2cm, 1fr, 4cm),
  cab[Camada], cab[O que é no meu projeto], cab[Quem gerencia],
  [IaaS], [a VM, a rede e o disco onde a stack roda (o servidor compartilhado da disciplina, com IP e domínio públicos)], [Fatec / professor],
  [PaaS], [Docker e Portainer (plataforma de containers que faz o build e o redeploy a partir do GitHub) e o MariaDB (banco fornecido pronto, do qual uso só o schema)], [Fatec (plataforma e banco); eu defino a stack e as tabelas],
  [Auto-hospedado], [Redis e MinIO, que subo em containers e opero eu mesmo (volume, imagem, credenciais)], [eu],
  [SaaS], [o #produto, para o cliente final; e os SaaS que uso: Stripe (pagamentos), GitHub (código e issues de entrega) e Mailtrap (e-mail de teste)], [eu (o produto); fornecedores (os serviços)],
)

= Quadro de entregas

Atividades obrigatórias do 2º bimestre. A data realizada é a do commit (atividades 7 e 8) ou da issue de entrega (atividades 9 a 11). As atividades 8 e 10 foram entregues após a data planejada, o que desconta 0,25 da nota da P2 cada uma, conforme a regra do enunciado.

#block(breakable: false, table(columns: (auto, 1fr, auto, auto, auto),
  align: (center, left, center, center, center),
  cab[Nº], cab[Atividade], cab[Data planejada], cab[Data realizada], cab[Situação],
  ..for a in atividades { (str(a.n), a.titulo, a.plan, a.real, a.sit) },
))

= Atividades realizadas

#let ficha(a) = block(breakable: false, table(columns: (auto, 1fr), stroke: 0.5pt + luma(150),
  table.cell(fill: luma(245), strong[Descrição]), a.desc,
  table.cell(fill: luma(245), strong[Data planejada]), a.plan,
  table.cell(fill: luma(245), strong[Data realizada]), a.real,
  table.cell(fill: luma(245), strong[Situação]), a.sit,
  table.cell(fill: luma(245), strong[Evidência]), a.evid,
  table.cell(fill: luma(245), strong[Link]), link(a.url),
))

== Atividade 7 — Plano Premium — cobrança de verdade com Stripe
#ficha(atividades.at(0))

*O que foi feito.* Criei o plano pago em modo de teste do Stripe (R\$ 9,90 por mês) e a rota que cria uma Checkout Session para o usuário logado e o redireciona ao pagamento. O webhook recebe a confirmação, valida a assinatura (`Stripe-Signature`) e só então marca o usuário como premium na tabela `assinaturas`, que guarda apenas o status e os ids do Stripe. Decidi que o Premium nunca é concedido pelo redirecionamento de volta do checkout, e sim somente pelo webhook assinado. O benefício verificável era o limite de favoritos no plano grátis, aplicado no backend, como a diferença entre admin e usuário da atividade 4.

#fig("a7-evidencia.png", [Atividade 7 — evidência da entrega (link, data e hora visíveis).], w: 90%)
#fig("a7-resultado.png", [Atividade 7 — resultado (o sistema funcionando).], w: 90%)

*Dificuldades e como foram resolvidas.* O Stripe normalmente exige uma URL HTTPS pública para o webhook, e o servidor era acessado por IP e porta; usei o endereço HTTPS do domínio da disciplina. Também foi preciso receber o corpo cru da requisição para validar a assinatura, e testei isso com um payload assinado de verdade (HMAC) nos testes automatizados.

== Atividade 8 — SaaS, PaaS, IaaS — e a documentação que o projeto nunca teve
#ficha(atividades.at(1))

*O que foi feito.* Escrevi no README a classificação de cada peça do sistema em IaaS, PaaS, CaaS e SaaS, com uma frase de justificativa, e a documentação reversa feita lendo o código: especificação do ponto de vista de quem usa, diagrama de arquitetura, regras de negócio no formato "se X, então Y" e modelo de dados. A leitura do código também revelou problemas, que ficaram registrados em "Limitações conhecidas": senhas em texto puro, a tabela de usuários apagada a cada reinício do auth-service e o código 2FA sem prazo de validade.

#fig("a8-evidencia.png", [Atividade 8 — evidência da entrega (link, data e hora visíveis).], w: 90%)
#fig("a8-resultado.png", [Atividade 8 — resultado (a documentação publicada no README).], w: 90%)

*Dificuldades e como foram resolvidas.* Extrair as regras do código, e não da memória, exigiu ler as rotas e os validadores de cada serviço. *Entregue com atraso* (planejada em 16/10, realizada em 21/10): a documentação foi escrita só no dia 21/10, depois de priorizar a estabilização da stack no Portainer.

== Atividade 9 — Fork e plano de negócio
#ficha(atividades.at(2))

*O que foi feito.* Criei o repositório novo e público do produto com todo o histórico do repositório anterior (a cópia espelhada pedida no enunciado, já que o botão _Fork_ do GitHub não copia um repositório para a mesma conta) e troquei o README: nome e frase do #produto, a dor, a persona (Camila, 21 anos, aluna noturna de ADS), cinco concorrentes e alternativas, a proposta de valor, o modelo de receita com Stripe (Free e Pro), as métricas de sucesso, o Lean Canvas com os 9 blocos e o mapa de reaproveitamento de cada peça do projeto atual. Abri 8 issues de backlog e a issue de entrega, mencionando o professor, e deixei no README antigo uma linha apontando para o repositório novo.

#fig("a9-evidencia.png", [Atividade 9 — evidência da entrega (link, data e hora visíveis).], w: 90%)
#fig("a9-resultado.png", [Atividade 9 — resultado (histórico de commits do repositório novo e lista de issues).], w: 90%)

*Dificuldades e como foram resolvidas.* Escolher um negócio plausível e quantificar a dor sem inventar dados: marquei os números de custo como hipóteses a validar com entrevistas na turma. O nome do repositório (`Smart-STUDY-Match`) ficou diferente do nome do produto no README (#produto), o que não afeta o sistema.

== Atividade 10 — Seu negócio no ar — o domínio no lugar dos filmes
#ficha(atividades.at(3))

*O que foi feito.* Troquei o repositório da stack do Portainer para o novo, sem criar stack nem trocar de subdomínio, e substituí o catálogo de filmes pelo recurso principal do negócio, o grupo de estudo. Criei as tabelas `disciplinas`, `grupos` e `grupo_membros` com chaves estrangeiras e o script de migração e seed `db/001_dominio.sql`, a API REST com CRUD completo em `/api/grupos`, as telas de listar, criar, detalhar e editar, os três papéis no auth-service (`admin`, `lider` e `estudante`, escolhidos no cadastro), o isolamento por usuário (403 ao abrir o grupo de outra pessoa), eventos de negócio no log e o upload da capa do grupo no MinIO, ligado ao registro certo. A landing page pública ficou na raiz do domínio, e removi o código, as telas, as rotas e a variável do TMDB.

#fig("a10-evidencia.png", [Atividade 10 — evidência da entrega (link, data e hora visíveis).], w: 90%)
#fig("a10-landing.png", [Atividade 10 — tela pública de acesso (login e cadastro com escolha de papel) no ar.], w: 90%)
#fig("a10-403.png", [Atividade 10 — resposta 403 (Forbidden) quando um estudante abre a tela restrita /admin/logs.], w: 90%)
#fig("a10-log.png", [Atividade 10 — eventos de negócio no log (grupo criado, login, checkout, ação negada 403), vistos pelo admin.], w: 90%)

*Dificuldades e como foram resolvidas.* Os identificadores dos usuários precisavam ser estáveis, mas o auth-service apagava a tabela de usuários a cada reinício; passei a criá-la só se não existir e migrei o papel antigo `usuario` para `estudante`. Como `usuarios` pertence a outro serviço, `grupos.lider_id` é uma referência lógica e não uma chave estrangeira. *Entregue com atraso* (planejada em 06/11, realizada em 09/11): a migração do domínio, a troca de papéis e o redeploy foram concluídos apenas na noite de 09/11.

== Atividade 11 — SaaS completo — planos, limites e assinatura com Stripe
#ficha(atividades.at(4))

*O que foi feito.* Transformei o pagamento único em assinatura recorrente: plano Free (R\$ 0,00, líder cria até 3 grupos por mês) e Pro (R\$ 9,90 por mês, sem limite), com o produto e o preço criados no Stripe em modo de teste. O checkout usa `mode=subscription` e fica ligado a um Customer do Stripe guardado no banco; os quatro webhooks mantêm plano, status e ids na tabela `assinaturas`, com validação de assinatura e sem efeito duplicado (tabela `stripe_eventos`). O botão _Gerenciar assinatura_ abre o portal do cliente, onde ele troca de plano e cancela. O limite do Free é aplicado na API, que recusa o 4º grupo do mês com 403 e uma mensagem dizendo qual é o limite e como liberar. O painel `/admin/painel`, só para admin, mostra usuários por plano, assinaturas ativas, MRR de teste e últimos eventos.

#fig("a11-evidencia.png", [Atividade 11 — evidência da entrega (link, data e hora visíveis).], w: 90%)
#fig("02-limite-plano-free-403.png", [Atividade 11 — limite do plano Free bloqueando o 4º grupo.], w: 90%)
#fig("03-checkout-stripe-cartao-4242.png", [Atividade 11 — checkout de assinatura com o cartão de teste 4242 (e-mail e nome borrados).], w: 80%)
#fig("04-perfil-plano-pro.png", [Atividade 11 — perfil já no plano Pro depois do webhook.], w: 90%)
#fig("07-stripe-webhook-200.png", [Atividade 11 — webhook `checkout.session.completed` entregue, com resposta 200.], w: 90%)
#fig("06-stripe-clientes-teste.png", [Atividade 11 — Stripe em modo de teste: cliente criado (e-mail borrado).], w: 90%)
#fig("08-perfil-volta-ao-free.png", [Atividade 11 — conta de volta ao Free depois do cancelamento.], w: 90%)

*Dificuldades e como foram resolvidas.* O redeploy no Portainer falhou com `no space left on device`: o disco do servidor compartilhado estava cheio de imagens antigas. Resolvi removendo as imagens e containers meus que não estavam em uso e repetindo o _Pull and redeploy_. Também foi preciso configurar o portal do cliente no Stripe (cancelamento imediato, para testar na hora) e garantir a idempotência dos webhooks. O print do painel admin não foi incluído nesta versão do relatório.

= Considerações finais

Neste bimestre aprendi que uma assinatura é um estado, e não um pagamento: o dinheiro entra pelo Stripe, mas quem mantém o plano certo no meu banco são os webhooks, que precisam ser validados, idempotentes e tolerantes à ordem de chegada. Aprendi também a separar o que é do app do que é de outro serviço (por exemplo, a tabela de usuários), a aplicar permissões e isolamento no backend e a documentar um sistema lendo o código real. Entreguei duas atividades com atraso (8 e 10), por ter deixado a documentação e a migração do domínio para o fim.

Para o #produto ser um produto de verdade, ainda faltam: o _match_ em si (o estudante descobrir e pedir entrada em grupos compatíveis, hoje ele só vê os grupos em que já é membro); guardar as senhas com hash; remover os valores padrão de credenciais do `docker-compose.yml`; expirar o código 2FA e deixar de mostrá-lo na tela; e as extras que não fiz, como health checks, CI e Swagger. Se eu fosse recomeçar, começaria pelos testes e pela separação de segredos, para não ter que corrigir depois.

= Declaração de autoria

Declaro que este relatório foi elaborado por mim, individualmente, e que as evidências apresentadas correspondem a entregas de minha autoria, verificáveis nos links informados.

#v(1.8cm)
#grid(columns: (1fr, 1fr), gutter: 1.5cm,
  [#line(length: 100%, stroke: 0.6pt) #v(0.3em) #align(center)[#aluno]],
  [#line(length: 100%, stroke: 0.6pt) #v(0.3em) #align(center)[Pompeia, 12/11/2026]],
)
