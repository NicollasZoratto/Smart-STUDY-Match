# 📚 StudyMatch

> **Encontre seu grupo de estudos ideal: match por disciplina e horário.**

Projeto da disciplina ISW055 (Introdução à Computação em Nuvem — FATEC), acompanhado pelo professor [github.com/siriani](https://github.com/siriani).
Este repositório é a continuação do **NicoFlix** (catálogo de filmes do Tom Hanks), espelhado com todo o histórico de commits. Arquitetura, documentação reversa e instruções de deploy do projeto original estão em [`docs/README_NicoFlix_filmes.md`](docs/README_NicoFlix_filmes.md).

**🌐 Sistema no ar:** https://nicollas-carvalho-isw055.lapps.studio — veja a seção [Atividade 10](#atividade-10--negócio-no-ar-studymatch).

---

## 1. Nome e frase

**StudyMatch** — um "Tinder" de grupos de estudo: você informa as disciplinas e os horários em que pode estudar, e a plataforma sugere pessoas e grupos compatíveis, para você entrar em um grupo ativo em minutos.

## 2. A dor

**Quem sofre:** estudantes de cursos superiores noturnos e semipresenciais (ex.: tecnólogos da FATEC), que estudam depois do trabalho e têm pouquíssimo tempo livre.

**Quando:** nas semanas que antecedem provas e entregas de trabalhos em grupo, quando surge a dúvida e não há com quem estudar.

**Quanto custa hoje** (hipóteses a validar com entrevistas na turma, não dados medidos):
- **Tempo:** horas por semana procurando parceiros por mensagens em grupos de turma, e mais horas combinando um horário que sirva para todos.
- **Dinheiro:** quem desiste de estudar em grupo recorre a aulas particulares ou plataformas pagas de reforço, ou perde nota por não entender a matéria.
- **Risco:** reprovação em disciplina, evasão, e trabalhos em grupo feitos às pressas com colegas que não se conhecem.

**Como resolvem hoje:** pedem parceiros no WhatsApp da turma e esperam alguém responder; os grupos que se formam muitas vezes esfriam depois de duas semanas, porque ninguém consegue combinar horário.

## 3. Persona

**Camila Ribeiro, 21 anos, 3º semestre de Análise e Desenvolvimento de Sistemas (noturno).**
Trabalha como assistente administrativa das 8h às 17h e entra na aula às 19h. Mora longe da faculdade, então só consegue estudar online, à noite, depois das 21h, ou aos sábados de manhã.
Em Banco de Dados, tem dificuldade com junções (JOIN) e prova marcada em duas semanas. Já mandou mensagem no grupo da turma, recebeu dois "também quero!", e o grupo nunca saiu do papel porque cada um só podia em um horário diferente.
O que a atrapalha: não sabe quem mais está na mesma dificuldade, não consegue achar um horário comum, e perde a motivação quando estuda sozinha.

## 4. Concorrentes e alternativas

| Alternativa | O que faz bem | O que faz mal |
|---|---|---|
| Grupos de WhatsApp da turma | Todo mundo já usa, é gratuito | Mensagens se perdem, não filtra por disciplina nem horário, não mostra quem está disponível |
| Servidores de Discord de estudo | Salas de voz, comunidade grande | Genérico e barulhento; difícil achar alguém da *sua* matéria e do *seu* horário |
| Planilhas / formulários de horários (Google Sheets) | Flexível e gratuito | Trabalho manual de alguém organizar; fica desatualizado rápido |
| Aulas particulares e plataformas de reforço | Atendimento direto, explicação individual | Caro e individual: não cria rede de apoio entre colegas |
| "Jeito de sempre": estudar sozinho ou combinar com amigos próximos | Sem custo e sem burocracia | Limitado ao círculo que você já conhece |

## 5. Proposta de valor

Diferente de grupos de mensagem e planilhas, o StudyMatch encontra para você **colegas da mesma disciplina com horário em comum**, em poucos toques, e mantém o grupo organizado.

## 6. Modelo de receita com Stripe

Assinatura mensal recorrente cobrada pelo Stripe (já integrado no projeto, em modo teste).

| | **Free** | **Pro — R$ 9,90/mês** |
|---|---|---|
| Participar de grupos | até **2** grupos ao mesmo tempo | **ilimitados** |
| Curtidas (swipes) por dia | até 10 | ilimitadas |
| Criar grupos próprios | 1 grupo | ilimitados |
| Filtros avançados (horário exato, nível, modalidade) | — | ✔ |
| Selo 👑 Pro no perfil | — | ✔ |

**Por que alguém pagaria:** quem tem prova marcada e pouco tempo precisa participar de vários grupos (uma disciplina por grupo) e achar parceiros rápido. O limite do Free deixa o produto útil, mas pressiona quem tem mais de duas disciplinas difíceis no semestre. O preço de R$ 9,90 equivale a menos de uma hora de aula particular.

**Meta realista:** converter de 3% a 5% dos usuários ativos para o Pro.

## 7. Métricas de sucesso

| Métrica | Como medir | Meta inicial |
|---|---|---|
| Cadastros | usuários criados por semana | 50 na primeira turma-piloto |
| Grupos ativos | grupos com pelo menos 3 membros e 1 encontro marcado | 10 |
| Taxa de match → grupo | matches que viram participação em grupo | 30% |
| Assinantes Pro | linhas com `premium = 1` | 2 a 3 (3 a 5% dos ativos) |
| **MRR** (receita recorrente mensal) | assinantes Pro × R$ 9,90 | R$ 30 a R$ 50 no primeiro mês |
| Retenção em 30 dias | usuários que voltam 30 dias após o cadastro | 40% |

## 8. Lean Canvas

| Bloco | Conteúdo |
|---|---|
| **Problema** | 1) Achar colegas da mesma disciplina que também querem estudar. 2) Combinar um horário comum. 3) Manter o grupo ativo depois das primeiras semanas. Hoje: WhatsApp, planilhas e sorte. |
| **Segmentos de clientes** | Estudantes de graduação e tecnólogo, principalmente noturnos, que trabalham de dia. Primeiros adotantes: alunos do curso de ADS da FATEC. |
| **Proposta única de valor** | Match por disciplina e horário: você chega a um grupo de estudo ativo em minutos. |
| **Solução** | 1) Perfil com disciplinas e horários livres. 2) Match/swipe de colegas e grupos compatíveis. 3) Grupos com vagas, horário fixo e e-mail de aviso a cada novo match. |
| **Canais** | Indicação dentro da turma, divulgação nos grupos de WhatsApp dos cursos, cartazes e QR code na faculdade, centros acadêmicos. |
| **Fontes de receita** | Assinatura Pro de R$ 9,90/mês via Stripe. |
| **Estrutura de custos** | Servidor/VM (fornecido pela disciplina, custo zero na fase acadêmica; em produção, VM + banco), taxa do Stripe por transação, e-mail transacional, tempo de desenvolvimento. |
| **Métricas-chave** | Cadastros, grupos ativos, taxa de match → grupo, assinantes Pro, MRR, retenção em 30 dias. |
| **Vantagem injusta** | Acesso direto ao público (o autor é aluno da turma), conhecimento do calendário real de provas e o histórico de disciplinas e horários que a plataforma acumula (os dados dos usuários). |

## 9. Mapa de reaproveitamento

| Peça do projeto atual (NicoFlix) | O que vira no SaaS | Como fica no StudyMatch |
|---|---|---|
| Catálogo de filmes (TMDB) | Recurso principal do negócio | **Grupos de estudo e disciplinas**: disciplina, horário, vagas, modalidade (online/presencial). Os dados passam a vir do nosso próprio banco, sem API externa |
| Favoritos | Interação principal | **Curtidas/swipe** em grupos e colegas (com limite diário no Free) |
| Comentários | Comunicação | **Mensagem de apresentação** ao pedir entrada num grupo |
| Microsserviço de login + 2FA + redefinição de senha (e-mail) | Identidade | Mantidos; o e-mail também notifica os matches |
| RBAC (admin / usuario) | Papéis do negócio | **admin**, **líder de grupo** (cria e modera o grupo) e **estudante** |
| Logs e auditoria (Redis Streams) | Eventos de negócio | "match criado", "pedido de entrada", "entrada aceita", "grupo criado", "limite do plano atingido" |
| Upload e perfil (MinIO) | Arquivos do domínio | Foto de perfil, foto/capa do grupo, e anexos de material de estudo (PDF de resumo) |
| Plano Premium (Stripe) | Assinatura | **StudyMatch Pro**: grupos e curtidas ilimitados, filtros avançados, selo |
| Documentação reversa (Atividade 8) | Manutenção | Continua valendo; será atualizada a cada entrega |
| Testes automatizados (pytest) | Qualidade | Continuam, com novos testes para match e limites |
| Deploy via Portainer + Docker Compose | Entrega | Mesma stack, mesma infraestrutura e mesmo subdomínio |

## 10. Próximas entregas

O roteiro (backlog) está nas issues deste repositório e resumido em [`docs/BACKLOG.md`](docs/BACKLOG.md).


---

## Atividade 10 — Negócio no ar (StudyMatch)

**URL do sistema:** https://nicollas-carvalho-isw055.lapps.studio (landing page pública, sem login).

### O que mudou do NicoFlix para o StudyMatch
O catálogo de filmes saiu; entrou o recurso principal do negócio, o **grupo de estudo**. Login, papéis, logs, upload e Stripe foram mantidos e mudaram de assunto. A stack no Portainer é a mesma, apontando para este repositório.

### Arquitetura atualizada

```mermaid
flowchart LR
    U([Navegador]) -->|HTTPS| WEB
    subgraph Stack["Stack única no Portainer (VM) — rede interna"]
        WEB["web / app_principal<br/>landing, telas, API /api/grupos"]
        AUTH["auth_service<br/>login, 2FA, papéis admin, lider, estudante"]
        LOG["log_service"]
        REDIS[("Redis<br/>eventos de negócio")]
        MINIO[("MinIO<br/>capas dos grupos e fotos")]
    end
    DB[("MariaDB<br/>disciplinas, grupos, grupo_membros,<br/>perfis, assinaturas, usuarios")]
    STRIPE[/"Stripe (plano Pro)"/]
    SMTP[/"Mailtrap (e-mail)"/]
    U -.->|URL pré-assinada da imagem| MINIO
    U -->|checkout hospedado| STRIPE
    WEB -->|valida o JWT a cada requisição| AUTH
    WEB -->|POST /log| LOG
    WEB -->|upload e URL assinada| MINIO
    WEB -->|SQL| DB
    WEB -->|cria Checkout Session| STRIPE
    STRIPE ==>|webhook assinado /stripe/webhook| WEB
    AUTH -->|usuarios, reset_tokens| DB
    AUTH --> SMTP
    AUTH --> LOG
    LOG --> REDIS
```

### Papéis (auth-service)
| Papel | Como se obtém | Pode |
|---|---|---|
| `admin` | primeiro cadastro do sistema | ver e gerenciar todos os grupos, ver os logs |
| `lider` | escolhido no cadastro | criar, editar e apagar **os próprios** grupos (plano grátis: 1 grupo; Pro: ilimitados) |
| `estudante` | escolhido no cadastro | ver os grupos de que participa; **não** cria, edita nem apaga grupos |

As regras valem na API: ação proibida responde **403** mesmo chamando direto, sem passar pela tela. O usuário só vê e altera os próprios dados: abrir o ID de um grupo de outra pessoa responde **403** (registro inexistente responde 404).

### Modelo de dados e migração
Script versionado: [`db/001_dominio.sql`](db/001_dominio.sql) (tabelas `disciplinas`, `grupos`, `grupo_membros`, com chaves estrangeiras, e seed de disciplinas). O `app_principal` roda os `db/*.sql` em ordem ao iniciar; quem clonar o repositório recria o banco subindo a stack, ou manualmente com `mysql ... < db/001_dominio.sql`. `db/000_limpeza_legado.sql` remove as tabelas do projeto anterior.

### API REST de grupos
Autenticada pela sessão do navegador (ou `Authorization: Bearer <JWT>`).

| Método e rota | Função | Respostas |
|---|---|---|
| `GET /api/grupos` | lista os grupos que o usuário pode ver | 200, 401 |
| `POST /api/grupos` | cria (`titulo, disciplina_id, dia_semana 0-6, horario_inicio, horario_fim, vagas, modalidade, descricao`) | 201, 400, 403 (papel ou limite do plano grátis) |
| `GET /api/grupos/<id>` | detalha | 200, 403 (de outro usuário), 404 |
| `PUT /api/grupos/<id>` | edita | 200, 400, 403, 404 |
| `DELETE /api/grupos/<id>` | remove | 204, 403, 404 |
| `POST /api/grupos/<id>/foto` | capa do grupo (multipart `foto`, até 2 MB, JPEG/PNG/WEBP) → MinIO | 200, 400, 403 |
| `GET /api/disciplinas` | disciplinas disponíveis | 200 |

Para testar direto, com o login feito no navegador, abra o console (F12) e rode, por exemplo, `fetch('/api/grupos/1').then(r => console.log(r.status))`.

### Telas
`/` (landing pública) · `/grupos` (lista) · `/grupos/novo` · `/grupos/<id>` (detalhe e capa) · `/grupos/<id>/editar` · `/perfil` · `/admin/logs` (admin).

### Eventos de negócio no log
`grupo_criado`, `grupo_editado`, `grupo_removido`, `foto_grupo_enviada`, `limite_grupos_gratis_atingido`, `assinatura_*`, `403_*` (acessos negados), além de login e logout. O admin vê tudo em `/admin/logs`, com usuário, ação, IP e data.

### Plano Pro (Stripe)
Free: 1 grupo próprio por líder. Pro, R$ 9,90/mês: grupos ilimitados e selo 👑. O Pro só é concedido pelo webhook assinado do Stripe (detalhes em [`docs/README_NicoFlix_filmes.md`](docs/README_NicoFlix_filmes.md)).

### Trocar a stack do Portainer para este repositório
Stacks → sua stack → *Editor* → em **Repository URL** coloque `https://github.com/NicollasZoratto/Smart-STUDY-Match` (branch `main`), mantenha as variáveis de ambiente (remova `TMDB_API_KEY` se existir) → *Pull and redeploy*.
