# TEMP — AI Engineer Challenge

## Estado atual

Implementação inicial do agente de atendimento da Empório da Música.

### Estrutura e componentes implementados

- Configuração de ambiente com `python-dotenv`.
- Integração inicial com Gemini usando `google-genai`.
- Logging com console e arquivo.
- Gerenciamento de sessões em memória, com UUID, histórico limitado a 20 mensagens e reset diário.
- Agente inicial com histórico de conversa e system prompt.
- Extração de texto do manual PDF utilizando PyMuPDF.
- Divisão do conteúdo em chunks.
- Geração local de embeddings utilizando Sentence Transformers.

### RAG — Progresso

**Documento:** `data/documents/políticas_da_loja.pdf`

- Total de páginas extraídas: 8.
- Acentuação preservada.
- Extração de texto validada.
- Tabelas perdem parte da estrutura durante a extração.
- Total de chunks gerados no teste: 13.
- Configuração inicial: `chunk_size=1200` e `overlap=150`.
- Metadados dos chunks: identificador, página de origem e conteúdo.
- Modelo de embeddings: `paraphrase-multilingual-MiniLM-L12-v2`.
- Dimensão dos embeddings: 384.
- Teste de geração com três textos executado com sucesso.

### Persistência vetorial

- ChromaDB integrado por meio de `PersistentClient`.
- Coleção `store_policies` criada.
- Métrica de distância configurada.
- Embeddings, documentos e metadados armazenados.
- Teste inicial: 13 chunks e 13 registros persistidos.
- Inserção realizada com `upsert`, utilizando IDs dos chunks.
- Persistência entre execuções confirmada.

### Dependências adicionadas

- `PyMuPDF`
- `sentence-transformers`
- `chromadb`

### Próximas etapas

1. Implementar armazenamento persistente dos chunks e embeddings no ChromaDB.
2. Implementar recuperação dos trechos mais relevantes a partir de uma pergunta.
3. Avaliar a recuperação com perguntas representativas do manual.
4. Integrar os trechos recuperados ao contexto enviado ao Gemini.
5. Testar respostas fundamentadas no manual, incluindo perguntas sem resposta disponível.
6. Melhorar a estratégia de chunking caso os testes indiquem problemas.

### Pontos de atenção

- Avaliar se o modelo de embeddings apresenta boa recuperação em português.
- Verificar se as tabelas e informações relacionadas estão sendo divididas de maneira adequada.
- Preservar a página de origem para rastreabilidade das informações.
- O manual contém possíveis ambiguidades, especialmente nas regras de parcelamento. Não assumir interpretações sem fundamento documental.
- Evitar carregar novamente o modelo de embeddings a cada pergunta.
- Não considerar a recuperação semântica garantia de resposta correta: avaliar a relevância dos trechos e o comportamento do agente quando não houver informação suficiente.
