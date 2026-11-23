# Questionário de ONA

Tudo o que é preciso para rodar a pesquisa de rede numa equipe com um formulário comum (Google Forms ou Microsoft Forms) e chegar às duas planilhas que a ONA de bolso lê.

Modelos prontos nesta pasta:

- [`modelo-ona.xlsx`](modelo-ona.xlsx): as duas abas (`pessoas` e `ligacoes`) num arquivo só;
- [`modelo-pessoas.csv`](modelo-pessoas.csv) e [`modelo-ligacoes.csv`](modelo-ligacoes.csv): as mesmas tabelas em CSV.

Uma base completa, de 114 pessoas fictícias, está em [`ona_de_bolso/exemplo/`](../ona_de_bolso/exemplo/).

## As perguntas

Use de 2 a 4 perguntas de nomeação. As duas primeiras bastam para as três perguntas de gestor (silo, dependência de uma pessoa, gestor no fluxo). Cada pergunta vira um `tipo` na tabela de ligações.

**0. Identificação (obrigatória)**

> Seu código
>
> *Escolha seu nome na lista. O código entre parênteses serve só para juntar as respostas; ninguém vai ver resultado por pessoa.*

Lista suspensa com todas as pessoas convidadas, no formato `Nome Sobrenome (A001)`.

**1. Informação** (`tipo` = `informacao`, até 10 nomes)

> Nas últimas 4 semanas, com quem você trocou informação importante para fazer o seu trabalho?
>
> *Pense em quem você procurou ou quem procurou você: pessoas do seu time e de outras áreas. Marque até 10 nomes.*

**2. Ajuda** (`tipo` = `ajuda`, até 5 nomes)

> Quando você trava num problema de trabalho, a quem você costuma pedir ajuda?
>
> *Marque até 5 nomes. Pode repetir pessoas da pergunta anterior.*

**3. Ideias** (opcional; `tipo` = `ideias`, até 5 nomes)

> Com quem você costuma discutir ideias novas ou melhorias para o trabalho?

**4. Energia** (opcional; `tipo` = `energia`, até 5 nomes)

> Depois de conversar com quais colegas você costuma sair com mais energia para trabalhar?

**Frequência** (opcional, vira o `peso`)

> Com que frequência você fala com essa pessoa?
>
> 1 = uma vez no período · 2 = mensal · 3 = quinzenal · 4 = semanal · 5 = diária

A frequência só entra se o formulário permitir uma pergunta por nome escolhido (no Microsoft Forms, com ramificação; no Google Forms, fica trabalhoso). Na maioria das pesquisas, dá para deixar de fora: sem ela, toda ligação vale 1.

### Como escrever as perguntas

- **Período curto e concreto.** "Nas últimas 4 semanas" funciona melhor do que "em geral": a pessoa lembra de conversas reais, não de quem acha que deveria procurar.
- **Um comportamento por pergunta.** "Trocou informação" e "pediu ajuda" são coisas diferentes; juntar as duas numa pergunta mistura redes diferentes.
- **Lista fechada de nomes.** A pessoa escolhe colegas de uma lista, não digita. Digitação livre gera erro de grafia e homônimo, e a rede fica furada.
- **Limite de nomes.** 10 para informação e 5 para as outras. Sem limite, quem é caprichoso marca 40 pessoas e parece o centro da empresa.
- **Nada de pergunta negativa** ("com quem é difícil trabalhar?"). Ela não ajuda a responder nenhuma das perguntas de gestor e afasta quem responde.
- **Texto neutro.** Não escreva "quem é referência" nem "quem você admira": isso vira votação de popularidade.

## Como aplicar

### Quem convidar

Todas as pessoas do recorte que você quer entender (uma diretoria, duas áreas que precisam trabalhar juntas, a empresa inteira se for pequena), inclusive gestores. A lista de nomes do formulário é a mesma lista de convidados: quem fica de fora do convite também some como opção, e a rede perde as ligações dessa pessoa.

### Taxa de resposta

ONA pede mais resposta do que uma pesquisa de clima, porque quem não responde deixa a rede furada exatamente nas ligações que faria. A regra da ONA de bolso:

- **85% ou mais:** leitura normal.
- **De 70% a 85%:** o relatório avisa "leia com cautela".
- **Abaixo de 70%:** o relatório não conclui sobre pontes, isolados nem dependência de uma pessoa. Os números servem só para planejar a próxima rodada.

Para chegar lá: convite do líder da área (não só do RH), prazo de 1 a 2 semanas, dois lembretes e o número parcial de participação por área compartilhado com os gestores (sem dizer quem respondeu).

### Anonimato e pseudonimização

ONA não pode ser anônima: para montar a rede, é preciso saber quem citou quem. O que dá para garantir é **confidencialidade**:

- os resultados saem por área (só com 5 pessoas ou mais) e o relatório não traz tabela por pessoa;
- na análise, os nomes viram códigos (`A001`, `A002`...); a tabela que liga código a nome fica com uma pessoa só, do RH, e é apagada no prazo combinado;
- quem conduz a análise não manda resposta individual para gestor.

Antes de enviar, alinhe com o jurídico e com o encarregado de dados (DPO): finalidade, base legal, quem vê o resultado e por quanto tempo os dados ficam guardados.

### Comunicação

Texto de convite (adapte):

> Estamos fazendo uma pesquisa curta (5 minutos) para entender como a informação circula entre as áreas e onde dá para melhorar processos e integração.
>
> São duas perguntas: com quem você troca informação no trabalho e a quem pede ajuda. Você escolhe os nomes numa lista.
>
> As respostas não entram em avaliação de desempenho. Os resultados são mostrados por área, nunca por pessoa, e só [nome da pessoa do RH] tem acesso às respostas individuais, que serão apagadas em [data].
>
> Prazo: [data]. Dúvidas: [contato].

E, no fim, devolva o resultado agregado para quem respondeu. Quem vê o retorno responde a próxima rodada.

## O formulário

### Google Forms

1. Primeira pergunta: "Seu código", tipo **Lista suspensa**, com todas as pessoas no formato `Ana Souza (A002)`.
2. Uma pergunta por tipo de ligação, tipo **Caixas de seleção**, com as mesmas opções. Em "Validação de resposta", escolha **Selecionar no máximo** 10 (ou 5).
3. Com muita gente, divida as opções por área em seções ("Comercial", "Operações"...), cada uma com a mesma pergunta; o conversor junta as colunas pelo começo do título.
4. Exportar: aba **Respostas** > **Link para o Planilhas** > na planilha, **Arquivo** > **Fazer download** > **CSV**.

### Microsoft Forms

1. Primeira pergunta: "Seu código", tipo **Escolha** com **Lista suspensa**.
2. Uma pergunta por tipo de ligação, tipo **Escolha**, com **Várias respostas** ligado.
3. Exportar: **Respostas** > **Abrir no Excel** (baixa um `.xlsx`).

Escreva o código entre parênteses em toda opção. Assim o conversor acha a pessoa sem depender da grafia do nome.

## As duas planilhas

**pessoas** (vem do cadastro do RH, não do formulário). Inclua **todas** as pessoas convidadas, inclusive quem não respondeu.

| coluna | conteúdo | exemplo |
|---|---|---|
| `id` | código pseudonimizado (não use matrícula nem nome) | `A002` |
| `area` | área ou diretoria | `Comercial` |
| `cargo` | cargo ou nível | `Analista` |
| `gestor_id` | `id` do gestor imediato (vazio para o topo) | `A001` |
| `unidade` | site, cidade ou unidade (opcional) | `São Paulo` |
| `respondeu` | `sim` ou `nao` | `sim` |

**ligacoes** (vem das respostas, uma linha por nome citado)

| coluna | conteúdo | exemplo |
|---|---|---|
| `origem_id` | quem respondeu | `A002` |
| `destino_id` | quem foi citado | `B014` |
| `tipo` | a pergunta | `informacao` |
| `peso` | frequência de 1 a 5 (opcional) | `4` |

Separador vírgula ou ponto e vírgula, em UTF-8. O app e a linha de comando também aceitam um `.xlsx` com as abas `pessoas` e `ligacoes`.

O conversor monta a tabela de ligações a partir da exportação do formulário e marca quem respondeu:

```bash
ona-de-bolso converter-forms respostas.csv --pessoas pessoas.csv \
    --quem "Seu código" \
    --pergunta informacao="Nas últimas 4 semanas, com quem" \
    --pergunta ajuda="Quando você trava" \
    --saida ligacoes.csv --marcar-respondeu pessoas.csv
```

O texto depois de `=` é o começo do título da coluna no arquivo exportado. Funciona com `.csv` (Google) e `.xlsx` (Microsoft).

## Como ler o resultado

- **Comece pelo resumo para o gestor** (`--gestor` na linha de comando, ou "Baixar o resumo" no app): ele responde se há área em silo, se a rede depende de alguém e se os gestores estão no fluxo do time.
- **Silo** é a área muito abaixo do acaso nas conversas com outras áreas (menos de 25% do esperado). Toda área conversa mais com o próprio time; isso sozinho não é silo.
- **Ponto único de falha** é a pessoa cuja saída deixa um grupo sem nenhum caminho até o resto. O problema é a rede depender dela, não a pessoa.
- **Isolado** é sinal para conversar (pessoa nova, afastada, remota, que não respondeu), não diagnóstico.
- A rede mostra como a informação circula, não quem trabalha melhor. Nenhuma métrica daqui deve entrar em avaliação, promoção ou desligamento.
