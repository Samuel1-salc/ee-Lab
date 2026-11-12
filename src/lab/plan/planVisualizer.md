# PLAN — Visualizador de classificação Smile Random Forest (Google Earth Engine)

## 0. Missão e limites

Implementar, **dentro da classe `visualizer` existente em `repository_ee.py`**, uma funcionalidade reutilizável para visualizar amostras classificadas por `ee.Classifier.smileRandomForest`, com projeção 2D, identificação de acertos/erros, métricas de validação e, quando disponível, probabilidades por classe. **Executar as etapas deste plano**, inspecionando o repositório antes de editar. Não criar uma classe `NaiveBayesVisualizer` paralela nem duplicar o pipeline de classificação existente.

Fonte de referência: `Código-para-servir-de-base-para-a-criação-do-visualizer-para-o-EE.txt` (disponível nas fontes do projeto; se não estiver acessível no filesystem local, pedir seu caminho antes de adaptar detalhes). O arquivo implementa `NaiveBayesVisualizer` com `plot_breast_cancer`, `plot_iris` e `_adicionar_metricas`. A fonte é **referência de visualização**, não implementação de Random Forest nem código pronto para EE.

### Terminologia

Random Forest realiza **classificação supervisionada**, não clustering não supervisionado. Chamar a figura de *dispersão/projeção 2D das amostras classificadas*, e não de clusters descobertos pelo modelo. PCA reduz as variáveis espectrais a dois eixos para visualização; não representa necessariamente a fronteira de decisão nem a distribuição espacial geográfica.

## 1. Etapa de descoberta do repositório — antes de programar

No alguma parte do texto completo do planVisualizer vai te dizer sobre criar ou dar a entender a voce criar a etapa de classificação , porém vamos utilizar o arquivo em serc/lab/base/classification-v3.ipynb , neste notebook tem todas as etapas de construção de um classificador, vamos utilizar os resultados do classificador para inserir em uma plotagem do visualizer criado. 

Lembrando , não faça algo complexo, no código base em fonts/ irá perceber que a construção é de certa forma simples e correta, NÃO É NECESSARIO CRIAR TESTES ROBUSTOS NEM UTILIZAÇÃO DE LINT DE TESTES.


- [ ] Localizar `repository_ee.py`, a declaração exata da classe `visualizer` (respeitar a capitalização real), seus métodos e consumidores.
- [ ] Mapear como o projeto autentica/inicializa `ee`, treina `smileRandomForest`, monta `ee.Image`/`ee.FeatureCollection`, define `inputProperties`, `classProperty`, `scale`, geometria e separa treino/teste.
- [ ] Identificar convenções de estilo, tipos, dependências, testes, logs, diretórios de saída e API pública; preservar compatibilidade.
- [ ] Examinar se as amostras já possuem atributos espectrais, rótulo verdadeiro e classe prevista. Não duplicar `sampleRegions`, treino nem download se o projeto já os fornecer.
- [ ] Registrar no resumo final quais componentes reais foram reutilizados e quais precisaram de adaptação. Não inventar caminhos, assinaturas ou classes inexistentes.

**Entrega:** breve mapa do fluxo atual e proposta de assinatura antes da implementação.

## 2. Contrato de saída do classificador (`setOutputMode`)

| Modo | Retorno conceitual | Uso | Decisão |
|---|---|---|---|
| `CLASSIFICATION` | Identificador da classe prevista | `y_pred`, comparação com `y_true`, matriz de confusão | **Obrigatório / padrão** |
| `MULTIPROBABILITY` | Array de probabilidades por classe, na ordem de classes do classificador | Distribuição de probabilidades, confiança por classe, gráficos complementares | **Recomendado, quando suportado** |
| `PROBABILITY` | Probabilidade/confiança da classificação prevista | Colorir pontos por confiança | Opcional, menos informativo que `MULTIPROBABILITY` |
| `RAW` | Representação interna, como votos brutos de árvores | Análise exploratória do ensemble | Opcional; validar estrutura e significado empiricamente |
| `REGRESSION` | Valor numérico contínuo | Problema de regressão | Fora do escopo |
| `RAW_REGRESSION` | Valores internos de regressão | Diagnóstico de regressão | Fora do escopo |

**Regra de implementação:** `CLASSIFICATION` é a saída principal; `MULTIPROBABILITY` complementa o diagnóstico. A API não retorna ambos em uma única saída escalar: avaliar classificadores treinados/derivados com `setOutputMode` apropriado, aplicados ao **mesmo conjunto de validação**, preservando identificação das amostras. Verificar na documentação e na execução real se a alteração de modo no classificador treinado é aceita; caso contrário, configurar o modo antes de treinar ou treinar modelos equivalentes com mesma configuração e seed, documentando as implicações. Não presumir que todos os modos são suportados por qualquer classificador.

**Atenção:** a ordem das probabilidades deve corresponder exatamente à ordem interna das classes observadas pelo classificador. Não associar posições a IDs/nomes de classes por suposição (nem presumir códigos consecutivos). Verificar e documentar mapeamento; se não for possível garantir, omitir rótulos de probabilidades e emitir erro explicativo. Probabilidades do ensemble não são necessariamente probabilidades calibradas nem garantem acerto.

## 3. Fluxo de dados e responsabilidades

```text
Imagem multibanda + amostras rotuladas
                |
    treino e validação separados
                |
     smileRandomForest treinado
                |
  classificar amostras de validação
       |                    |
 CLASSIFICATION       MULTIPROBABILITY
       |                    |
 y_true / y_pred       probabilidades
       |                    |
       +----- amostras alinhadas -----+
                        |
       extração limitada de atributos
                        |
    NumPy/Pandas -> PCA ou 2 bandas
                        |
      métricas + Matplotlib -> PNG
```

- EE: treinamento/classificação, amostragem e, quando conveniente, métricas agregadas server-side.
- Python: converter **apenas amostras limitadas** para estruturas tabulares, validar, projetar em 2D, calcular/organizar métricas e plotar.
- Manter operações `ee.*` lazy até a etapa de materialização; não usar `getInfo()` em imagens inteiras ou coleções gigantes. Configurar limites, paginação/exportação para volumes altos e mensagens de erro claras.
- Não baixar todos os pixels de uma cena para fazer scatter plot. Usar amostras de validação com limites e seed reproduzível.
- Preservar identificador estável por amostra entre as saídas; nunca alinhar probabilidades e predições apenas pela ordem de duas consultas separadas sem garantia.

## 4. Adaptação concreta do código-base

| Trecho da fonte Naive Bayes | Reutilizar | Refatorar / não copiar literalmente |
|---|---|---|
| `__init__(figsize, dpi, output_dir)` (linhas 12–19) | Configuração de figura e diretório | Integrar às configurações da classe `visualizer`; `pathlib.Path.mkdir(parents=True, exist_ok=True)`; não sobrescrever estado existente |
| `_adicionar_metricas` (21–59) | Caixa com métricas no canto do gráfico | Métricas opcionais, validação independente, nomes de classe genéricos; tempo EE é latência observada, não tempo isolado de CPU do treino |
| `plot_breast_cancer` (62–138) | PCA 2D, cores, acertos `o` e erros `x`, legendas, salvamento | Remover pressupostos de 30 atributos, rótulos `M/B`, classes fixas e origem sklearn |
| `plot_iris` (140–223) | Dispersão usando duas variáveis diretamente, três cores, erros/acertos | Trocar índices fixos `[2,3]` por nomes de bandas escolhidos; remover espécies e unidades em cm |
| `plt.savefig`, `plt.close` | Exportação PNG e liberação de recursos | Retornar `Path`/objeto útil; evitar `print` obrigatório e nomes fixos; suportar `show=False` |
| `PCA(n_components=2)` | Projeção multibanda para 2D | Exigir ao menos 2 atributos numéricos válidos; considerar padronização opcional, ajustar PCA somente no conjunto adequado, documentar variância explicada |

**Não copiar:** datasets Breast Cancer/Iris, classificadores Naive Bayes/sklearn, mapas de cor codificados para classes específicas, valores de acurácia recebidos sem validação, nem tempos fictícios. O exemplo usa apenas `X_test`, `y_test`, `y_pred` já materializados: **não ensina a obter resultados de EE**; construir essa ponte explicitamente.

## 5. API da classe `visualizer`

- [ ] Preferir método público expressivo, por exemplo `plot_random_forest_classification(...)`, **dentro da classe existente**. Ajustar assinatura ao estilo do projeto.
- [ ] Aceitar preferencialmente `ee.FeatureCollection` de validação já classificada, `feature_columns`, `label_property`, `prediction_property`, `class_names` opcional, `projection='pca'|'bands'`, `plot_bands`, `output_path`, `max_samples`, `seed` e `show=False`.
- [ ] Se o repositório já expuser classificador treinado e amostras não classificadas, permitir um adaptador interno que execute a classificação antes da plotagem, sem duplicar a lógica de treinamento.
- [ ] Separar helpers privados para: extração EE→tabela; validação de colunas/labels; projeção; cálculo de métricas; renderização; salvamento.
- [ ] Reaproveitar métodos existentes da classe; não criar abstrações excessivas ou dependências novas sem necessidade.
- [ ] Retornar um resultado estruturado (caminho da figura, métricas, contagens, método de projeção, variância explicada, avisos), coerente com os padrões do repositório.

## 6. Plotagens a implementar

### MVP obrigatório — dispersão 2D

- [ ] Plotar cada amostra com cor da **classe verdadeira**; marcador `o` quando `y_true == y_pred`, `x` quando divergir.
- [ ] Legenda dinâmica para N classes, sem assumir apenas duas ou três.
- [ ] Modo `pca`: duas componentes principais, com porcentagem de variância explicada nos eixos. Usar somente bandas/features preditoras, **nunca** rótulo, predição ou probabilidades no PCA.
- [ ] Modo `bands`: selecionar duas bandas/índices nomeados (ex.: NIR e RED, NDVI e NDWI se realmente existirem), com eixos e unidades corretos.
- [ ] Título, legenda, grade, total de amostras, número de classes, indicação de treino/validação, seed e aviso de que a figura é uma projeção.
- [ ] Exportar PNG com resolução configurável, fechar a figura e retornar o caminho.

### Métricas obrigatórias

- [ ] Matriz de confusão com ordem de classes explícita, contagem por classe, acurácia global e, se houver suporte adequado, precisão/recall/F1 por classe e macro-F1.
- [ ] Calcular métricas **somente em dados de validação/teste independentes**; não apresentar acurácia de treinamento como desempenho generalizado.
- [ ] Caso se use `ee.ConfusionMatrix`, verificar orientação linhas/colunas e correspondência de classes; não usar matriz de treinamento como matriz de validação.
- [ ] Tempos de treino e predição apenas se efetivamente medidos. Como EE executa remotamente e lazy, identificar tempos como latências observadas de operações materializadas; caso contrário omitir.
- [ ] Se usar subamostragem para visualização, distinguir acurácia no conjunto completo de validação e acurácia no subconjunto plotado.

### Complementos recomendados

- [ ] Heatmap de matriz de confusão (pode ser segunda figura).
- [ ] Quando `MULTIPROBABILITY` estiver validado, gráfico de probabilidades por classe e/ou intensidade de confiança no scatter; não chamar confiança de acurácia.
- [ ] Distribuição de erros por classe e, opcionalmente, importância das variáveis via `classifier.explain()` quando houver informação compatível.
- [ ] `RAW` somente em módulo exploratório, com documentação do formato retornado e sem assumir que votos são probabilidades calibradas.


## 8. Sequência operacional para o Codex CLI

1. **Inspecionar** `repository_ee.py`, chamadas existentes e o arquivo-fonte Naive Bayes.
2. **Propor** assinatura e fluxo de dados conforme as abstrações já existentes.
3. **Implementar MVP** na classe `visualizer`: extração limitada, validação, PCA/duas bandas, scatter de acertos/erros, PNG e métricas.
4. **Integrar EE** com `CLASSIFICATION` e validação independente; garantir ordem/identidade das amostras.
5. **Adicionar `MULTIPROBABILITY`** somente após confirmar suporte, formato e mapeamento de classes; tratar ausência com degradação graciosa.
6. **Adicionar diagnósticos** (matriz de confusão e probabilidades) sem bloquear o MVP.
7. **Testar e documentar** chamada real baseada no repositório, dependências, limites e interpretação dos gráficos.
8. **Entregar resumo** dos arquivos alterados, testes executados, resultados, decisões de refatoração e pendências verificáveis.

## 9. Restrições explícitas

- Não substituir o classificador GEE por `sklearn.RandomForestClassifier`.
- `sklearn.decomposition.PCA` pode ser usado **apenas para visualização** local; não treinar outro classificador.
- Não inventar probabilidades, métricas, tempos, nomes de bandas ou classes.
- Não tratar PCA como mapa geográfico nem clusters visuais como agrupamentos inferidos por algoritmo de clustering.
- Não introduzir autenticação EE, credenciais, chamadas `getInfo()` massivas ou exports custosos na importação do módulo.
- Manter código limpo, tipagem coerente, responsabilidade única, mensagens de erro acionáveis e compatibilidade com o repositório.

## 10. Referências a conferir durante implementação

- `ee.Classifier.setOutputMode`: https://developers.google.com/earth-engine/apidocs/ee-classifier-setoutputmode
- `ee.Classifier.smileRandomForest`: https://developers.google.com/earth-engine/apidocs/ee-classifier-smilerandomforest
- Guia de classificação: https://developers.google.com/earth-engine/guides/classification
- `ee.FeatureCollection.classify`: https://developers.google.com/earth-engine/apidocs/ee-featurecollection-classify
- `ee.ConfusionMatrix`: https://developers.google.com/earth-engine/apidocs/ee-confusionmatrix

**Definição de pronto:** uma chamada documentada ao método da classe `visualizer` produz um PNG de amostras Random Forest classificadas pelo GEE, diferencia visualmente acertos e erros, mostra métricas reais de validação e suporta classes/bandas dinâmicas; diagnósticos de probabilidades são gerados somente quando tecnicamente válidos.
