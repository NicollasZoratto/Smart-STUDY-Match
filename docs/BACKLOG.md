# Backlog (viram as issues do repositório)

1. **Modelar tabelas de disciplinas, grupos, horários e membros** — `disciplinas`, `grupos`, `grupo_membros`, `disponibilidades` (e relações). Substitui o catálogo do TMDB.
2. **Criar os papéis admin, líder de grupo e estudante (RBAC)** — líder cria e modera o próprio grupo; admin modera tudo; 403 no backend para o resto.
3. **Tela de descoberta com match por disciplina e horário** — lista/swipe de grupos e colegas compatíveis, com curtir e pular.
4. **Landing page pública do StudyMatch** — proposta de valor, planos Free e Pro e botão de cadastro.
5. **Plano Pro no Stripe com limites do Free** — 2 grupos e 10 curtidas por dia no Free; ilimitado no Pro; webhook assinado (reaproveita a integração atual).
6. **Perfil com foto e foto de capa do grupo (MinIO)** — reaproveita o upload atual.
7. **Eventos de negócio nos logs e e-mail de notificação de match** — reaproveita log_service/Redis e o SMTP.
8. **Corrigir pontos fracos herdados: hash de senha e não apagar `usuarios` a cada reinício** — ver "Limitações conhecidas" em `docs/README_NicoFlix_filmes.md`.
