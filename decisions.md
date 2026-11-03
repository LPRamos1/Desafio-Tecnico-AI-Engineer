# Decisões de Arquitetura — Empório da Música AI Agent

Registro das decisões do projeto, com contexto, justificativa e trade-offs.
Status: **Aceita** (em uso), **Em avaliação**, **Substituída**.

---

## DEC-001 — Gerenciamento e persistência de sessões

**Status:** Aceita

**Contexto:** O agente precisa manter o contexto para perguntas complementares ("e esse é bom pra iniciante?"). O escopo e o prazo são limitados.

**Decisão:**
- Classes `Session` e `SessionManager`, em memória (RAM), sem banco de dados.
- UUID para identificar cada sessão.
- Histórico limitado a 20 mensagens individuais (usuário e assistente).
- Reset automático do histórico quando a sessão é acessada em um dia diferente.
- Data de criação com fuso horário (`datetime` aware).

**Justificativa:** Persistir em banco acrescentaria complexidade sem benefício para um CLI de um usuário. O limite de mensagens controla o crescimento do contexto enviado ao modelo.

**Trade-offs:**
- Sessões se perdem ao encerrar o processo e não são compartilháveis entre instâncias.
- O reset acontece na primeira interação do novo dia, não à meia-noite.
- Limite por número de mensagens não garante limite de tokens.

**Arquivos:** `app/agent/session.py`, `app/config/settings.py`

---

## DEC-002 — Recuperação de conhecimento por RAG

**Status:** Aceita

**Contexto:** O assistente responde sobre políticas do manual em PDF (8 páginas extraídas). Clientes usam palavras diferentes das do documento.

**Decisão:** RAG: extração do texto, chunking por seção, embeddings, armazenamento vetorial e recuperação dos trechos para compor o contexto do LLM.

**Justificativa:** A busca semântica encontra trechos mesmo sem coincidência exata de palavras, e a arquitetura escala se o manual crescer.

**Trade-offs:**
- Um manual de 8 páginas caberia inteiro no prompt, o que seria mais simples e evitaria falhas de recuperação. RAG foi escolhido conscientemente, para demonstrar a arquitetura e por escalar melhor.
- Exige etapa de indexação e avaliação da qualidade do retrieval.
- A recuperação não garante que todas as regras relevantes cheguem ao modelo (ver DEC-005).

**Chunking:** por seção numerada (regex sobre títulos como "3.1 Parcelamento"), `chunk_size=1200`, `overlap=150`, preservando seção e página nos metadados. Resultado: 13 chunks. Seções maiores que o limite são divididas com sobreposição.

**Arquivos:** `app/knowledge/ingestion.py`, `embeddings.py`, `retrieval.py`

---

## DEC-003 — Geração local de embeddings

**Status:** Aceita

**Decisão:** Sentence Transformers com `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensões, vetores normalizados).

**Justificativa:** Suporta português, roda localmente sem API externa e mantém os embeddings independentes do provedor do LLM.

**Trade-offs:** Download do modelo na primeira execução e uso de CPU/memória locais. É um modelo pequeno; a qualidade em português foi avaliada só com poucas perguntas (ver DEC-005).

**Arquivos:** `app/knowledge/embeddings.py`, `app/config/settings.py`

---

## DEC-004 — Armazenamento vetorial persistente

**Status:** Aceita

**Decisão:** ChromaDB com `PersistentClient`, coleção `store_policies`, métrica de cosseno, `upsert` por ID.

**Configuração:**
- Metadados: página e seção de origem.
- Identificadores: `section-{numero}-chunk-{n}`.
- Diretório `vectorstore/` fora do Git.

**Justificativa:** Armazenamento local, simples e persistente entre execuções.

**Trade-offs:** É preciso reindexar (`python ingest.py`) quando o PDF ou o chunking mudam. A reindexação apaga e recria a coleção.

**Arquivos:** `app/knowledge/vector_store.py`, `ingest.py`

---

## DEC-005 — Busca híbrida: vetorial + BM25 com RRF

**Status:** Aceita (com limitação conhecida)

**Contexto:** Testes iniciais mostraram que a busca vetorial sozinha às vezes não trazia a seção 3.1 (parcelamento) entre os primeiros resultados.

**Decisão:** Combinar busca vetorial (ChromaDB) e lexical (BM25 via `rank-bm25`) usando Reciprocal Rank Fusion: cada chunk recebe `1 / (60 + posição)` em cada ranking, e as pontuações são somadas.

**Avaliação (mesmo conjunto de perguntas nas três estratégias):**
- BM25 sozinho: seção 3.1 em 1º para "Quais são as regras de parcelamento?", mas fora do Top 3 para "Posso parcelar uma compra em 5 vezes?".
- Híbrido com RRF: seção 3.1 no Top 3 em 4 de 5 consultas originais.
- Paráfrases adicionais:
  - "Posso parcelar uma compra em 5 vezes?": ausente do Top 3.
  - "Posso dividir o pagamento em cinco parcelas?": 2º lugar.
  - "Uma compra pode ser paga em 4, 5 ou 6 vezes?": ausente do Top 3.

**Mitigações adotadas (DEC-006):** o próprio LLM reescreve a consulta ao chamar a tool de políticas e o `top_k` passou de 3 para 5.

**Pendente:** medir de novo, de forma sistemática, depois dessas mitigações.

**Arquivos:** `app/knowledge/keyword_search.py`, `hybrid_search.py`

---

## DEC-006 — Function calling como mecanismo central do agente

**Status:** Aceita (substitui o fluxo "RAG em toda mensagem" da primeira versão)

**Contexto:** A primeira versão executava a busca de políticas antes de toda mensagem, inclusive "oi", e não acessava os CSVs. O desafio pede que o agente saiba *quando* consultar dados e *quando* consultar políticas.

**Alternativas consideradas:**

| Opção | Pontos fortes | Pontos fracos |
|---|---|---|
| RAG para tudo | Simples, bom para texto | Números e filtros exatos são frágeis com embeddings |
| Agente Text-to-SQL | Flexível, aproveita relações | SQL incorreto ou inseguro, custo, comportamento menos previsível |
| **Function calling** | Modelo escolhe a ferramenta, argumentos validáveis, separa interpretação de execução | Exige boas descrições de tool; o modelo pode escolher a errada |

**Decisão:** Function calling nativo do `google-genai`. Funções Python são passadas como tools; o SDK executa o laço modelo → tool → modelo, com `maximum_remote_calls=5`.

**Tools:** `buscar_produtos`, `consultar_promocoes`, `consultar_pedido`, `consultar_politicas` (esta envolve o retriever híbrido).

**Justificativa:** Dados estruturados ficam exatos e determinísticos; políticas continuam com RAG. A pergunta do cliente vira uma consulta curta e objetiva escrita pelo modelo, o que ajuda o retrieval.

**Por que sem LangGraph/LangChain agora:** o fluxo é um laço simples, e o SDK já o executa. Menos dependências e menos partes móveis no prazo disponível. LangGraph passa a fazer sentido com estados explícitos, ramificações e escalonamento a humano.

**Trade-offs:**
- O modelo pode escolher a tool errada ou passar argumentos ruins; mitigado por descrições detalhadas e pelo prompt.
- O laço automático do SDK dá menos controle fino do que um laço escrito à mão.

**Arquivos:** `app/tools/registry.py`, `app/agent/agent.py`, `app/llm/gemini_client.py`

---

## DEC-007 — Camadas tool → service → repository

**Status:** Aceita

**Decisão:**
- *Repository* (`data_repository.py`): lê e limpa os CSVs.
- *Service* (`catalog_service.py`, `order_service.py`): regras de negócio, sem dependência do LLM.
- *Tool* (`registry.py`): adaptador fino entre o modelo e os services.

**Justificativa:** Separar responsabilidades e permitir testar as regras sem chamar o LLM (requisito de testabilidade).

**Trade-offs:** Mais arquivos do que um único módulo; compensado pela clareza e pelos testes.

---

## DEC-008 — Tratamento dos dados

**Status:** Aceita

**Decisões:**
- Linhas sem `product_id` ou preço numérico são descartadas (ex.: rodapé de planilha no `products.csv`).
- Tipos convertidos explicitamente; duplicatas removidas.
- Descrições que citam uma marca diferente da do nome são ignoradas e registradas no log, em vez de mostradas ao cliente. A lista de marcas é fixa (`KNOWN_BRANDS`).
- Busca por categoria tolera acentos e plural por normalização e comparação de prefixo (`violão`/`violões`).
- Se o produto existe mas está indisponível, o resultado informa isso e sugere similares da mesma categoria, na faixa de ±30% de preço e em estoque.

**Trade-offs:** A heurística de marca depende da lista fixa e pode deixar passar inconsistências de outros tipos.

---

## DEC-009 — Promoções

**Status:** Aceita (com limitação)

**Contexto:** `is_active` não parece suficiente: promoções têm validade e regras de cumulatividade, e o desconto Pix não é cumulativo.

**Decisão:** Considerar apenas promoções com `is_active=1`; havendo mais de uma por produto, usar a de maior desconto, **sem somar**. O preço de promoção é mostrado junto do original. Antes de falar de desconto Pix ou parcelamento em produto promocional, o agente consulta a política.

**Limitação:** o CSV não traz datas de validade, então não é possível checar vigência.

---

## DEC-010 — Identificação do cliente em consultas de pedido

**Status:** Aceita (simulação)

**Contexto:** Dados de pedido são pessoais; não podem ser mostrados a qualquer pessoa que informe um número.

**Decisão:** Exigir número do pedido **e** e-mail ou telefone cadastrado, validados contra `customers.csv`. Se o pedido não existir ou os dados não conferirem, a resposta é a mesma. O identificador é mascarado nos logs. O agente só pede a identificação quando o cliente quer consultar um pedido.

**Justificativa:** Simula autenticação de forma simples, sem pedir login no início da conversa.

**Limitação:** não é segurança real. E-mail e telefone podem ser conhecidos por terceiros, e não há limite de tentativas.

---

## DEC-011 — Provedor e modelo de LLM

**Status:** Aceita

**Decisão:** Google Gemini via `google-genai`; modelo configurável por `GEMINI_MODEL`, fallback opcional por `GEMINI_FALLBACK_MODEL`, timeout de 60 s por requisição e temperatura baixa (0.2).

**Justificativa:** Camada gratuita e function calling nativo. Durante o desenvolvimento, um modelo mais novo retornou erros de congestionamento, e uma resposta demorou vários minutos. Timeout e fallback evitam que o atendimento fique preso.

**Trade-offs:** Um único provedor. A causa exata da demora observada (download do modelo de embeddings no primeiro startup ou latência da API) `[CONFIRMAR: ainda a verificar nos logs]`.

---

## DEC-012 — Limites defensivos

**Status:** Aceita (parcial)

**Implementado:** 2000 caracteres por mensagem, 20 mensagens de histórico, 5 chamadas de tool por mensagem, timeout de requisição.

**Não implementado (ver README):** token bucket por cliente, limites de tokens de entrada e saída.

**Justificativa:** Com um único usuário em CLI, token bucket não se justifica; está registrado como evolução.

---

## DEC-013 — Rastreabilidade e logging

**Status:** Aceita

**Decisão:** Logger único com dois destinos: terminal (resumido) e arquivo rotativo (5 MB, 3 backups, detalhado). Cada chamada de tool registra nome, argumentos (identificador mascarado) e início do resultado. Tempos de startup e de LLM são registrados.

**Justificativa:** Permite reconstruir por que o agente respondeu algo: qual tool usou e o que recebeu. Exceções dentro de uma tool não derrubam a conversa: o modelo recebe um erro genérico e responde com transparência.

---

## DEC-014 — Conflitos e ambiguidades no manual

**Status:** Aceita

**Contexto:** O manual contém inconsistências: telefone diferente nas seções 1 e 7; regras de parcelamento diferentes nas seções 3 e 3.1; condições de troca por preferência diferentes para loja física e online.

**Decisão:** Não escolher uma regra no escuro. O prompt orienta o modelo a explicar as condições aplicáveis e perguntar o que falta (por exemplo, o canal da compra). Para o telefone, `[CONFIRMAR: seção 7 tratada como a correta]`. As ambiguidades estão documentadas no README.

**Trade-offs:** O comportamento depende do modelo seguir o prompt. Falta medir isso com perguntas dirigidas.

---

## Pendências e próximos passos

- Medir o retrieval depois das mitigações da DEC-005 e comparar com colocar o manual inteiro no prompt.
- Montar conjunto de avaliação ponta a ponta (tool correta, resposta fiel às fontes, ausência de alucinação).
- Testes de prompt injection e de acesso indevido a pedidos.
- Persistência de histórico e API (FastAPI).
- Migração para LangGraph, se o fluxo ganhar estados e escalonamento a humano.