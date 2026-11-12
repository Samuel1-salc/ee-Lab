# Step 1 — Descoberta do visualizador Random Forest

Inspeção estática realizada em 12/11/2026, referente a
`planVisualizer.md#step-1`. Nenhuma operação remota EE foi executada.

## Componentes encontrados

- `src/lab/base/repository_ee.py`: a declaração real é `class Visualizer`,
  ao final do módulo. Contém somente uma docstring, sem construtor, métodos,
  configuração ou estado a preservar. Nenhum consumidor de `Visualizer` foi
  encontrado nos arquivos Python, notebooks e Markdown pesquisados em `src/lab/`.
- `src/lab/base/classification-v3.ipynb`: consumidor de `Models`, `Landsat8`,
  `LocalLabels`, `MapLayers`, `GeometryUtils` e `PeriodoAgricola`. Fornece o
  pipeline que deve ser reutilizado, sem criar outro classificador.
- `src/lab/fonts/Código-para-servir-de-base-para-a-criação-do-visualizer-para-o-EE.txt`:
  referência local acessível, com `NaiveBayesVisualizer`, `_adicionar_metricas`,
  `plot_breast_cancer` e `plot_iris`.

## Fluxo atual do notebook

1. Importa `ee` e os utilitários de `repository_ee`. Chama
   `initialize_earth_engine(use_eerepr=True)`, sem projeto explícito.
   Esse helper chama `ee.Initialize()` nesse caso. A autenticação não ocorre
   nessa célula; o módulo oferece `AuthenticateEarhEngine(force=False)`
   separadamente. A constante `PROJECT` não é aplicada automaticamente pelo helper.
2. Define AOI poligonal no Tocantins, ano 2025, escala 30 m, seed 42,
   fração de treino 0,70 e 1000 amostras solicitadas por classe.
3. Constrói `landsat` e `feature_space` por `Landsat8.collection` e
   `Landsat8.feature_space`. `bandas_preditoras = feature_space.bandNames()`
   é a lista server-side usada como `input_properties` no treino e na classificação.
4. Carrega assets de `projects/poetic-tesla-506814-e1/assets/`:
   `tocantins_2025_FLORESTA`, `tocantins_2025_AGRICULTURA` e
   `tocantins_2025_AGUA`. Define `landcover` como 0, 1 e 2, respectivamente.
   O acesso aos assets depende da conta EE; não foi verificado remotamente.
5. Separa polígonos inteiros por classe usando `randomColumn("split")`,
   seeds 42, 43 e 44 e limiar 0,70. Rasteriza treino e validação separadamente
   com `LocalLabels.from_feature_collection` e amostra com
   `Models.stratified_sample`, escala 30, `tile_scale=2`, `geometries=True`.
   Polígonos sobrepostos e independência espacial não foram verificados.
6. Treina `modelo_rf = Models.train(..., algorithm="rf")`, que usa
   `Models.create` → `Models.random_forest` → `ee.Classifier.smileRandomForest`.
   Parâmetros: 100 árvores, 5 variáveis por divisão, bag fraction 0,8,
   até 100 nós e população mínima de folha 10. O seed do modelo fica no
   padrão 0 do helper; não recebe o `SEED=42` da amostragem.
7. Produz `classificacao_rf` por `Models.classify_image` para o mapa.
8. Calcula `metricas_treino` e `metricas_validacao` separadamente.
   `Models.validation_metrics` classifica `amostras_validacao` e retorna
   `predictions`, matriz de confusão, acurácia, kappa e acurácias de produtor
   e consumidor. A ordem solicitada no notebook é `[0, 1, 2, 3]`.

## Entrada pronta para o visualizador

`metricas_validacao["predictions"]` é o ponto de integração preferencial:
uma `ee.FeatureCollection` derivada das amostras, com atributos preditores,
referência `landcover` e predição `classification` na mesma feição.
Não é necessário repetir amostragem, treinamento ou classificação.

As bandas-base definidas no módulo são `blue`, `green`, `red`, `nir`,
`swir1`, `swir2`, `temp`, `ndvi`, `evi2`, `cai`, `ndwi`, `mndwi`, `ndbi`,
`gcvi`, `hall_cover` e `pri`. O feature space combina mediana anual com
versões `_dry`, `_wet`, `_stdDev`, `_min`, `_max` e `_ampl`.
A disponibilidade real deve ser conferida pela lista `bandas_preditoras`;
`nir`/`red` e `ndvi`/`ndwi` são candidatos definidos no código.

Ainda faltam a extração limitada para tabela, validação local, projeção e
renderização. Não há propriedade própria de identificação estável criada
explicitamente pelo notebook; antes de combinar probabilidades obtidas em
consultas distintas, será necessário estabelecer e verificar essa identidade.
O fluxo atual não usa `setOutputMode` nem produz probabilidades.

## Referência visual e convenções

Reaproveitar o desenho com cor por classe verdadeira, círculos para acertos,
cruzes para erros, caixa de métricas, PCA com variância explicada, alternativa
com dois atributos, configuração de tamanho/DPI e fechamento após salvar PNG.
Adaptar classes e nomes dinâmicos, bandas nomeadas, métricas verificadas,
retorno útil e `show=False`. Descartar datasets, classes fixas, classificação
Naive Bayes, tempos recebidos sem comprovação e nomes fixos de arquivos.

O módulo utiliza type hints, docstrings, métodos estáticos/de classe e
resultados EE lazy; métricas são retornadas em dicionários. `TimeSeries.plot_ndvi`
já usa imports locais de geemap/Matplotlib e conversão `geemap.ee_to_df`,
mas não implementa o limite necessário ao novo scatter. `Export` já exporta
métricas em CSV, sem renderização PNG. Não foi encontrada configuração central
de logs ou diretório de gráficos.

Dependências observadas: `ee` e pandas no módulo; geemap e Matplotlib nos
helpers de visualização; NumPy, Matplotlib e PCA do scikit-learn na referência.
Não há manifesto de dependências nem suíte automatizada definidos pelo projeto.
Não é necessário introduzir infraestrutura de testes ou lint para esta etapa.

## Pendências encontradas no notebook

- Nas duas chamadas de `stratified_sample`, `class_values` contém três itens,
  mas `class_points` contém dois. As listas precisam ser reconciliadas antes
  de validar o pipeline remotamente.
- A célula do mapa referencia `poligonos_urban`, que não é definido no notebook.
- A checagem de polígonos exige apenas duas classes, embora sejam carregadas
  três; a mensagem ainda menciona urbano. A checagem posterior de amostras
  exige três classes.
- A matriz solicita quatro classes e o mapa configura quatro cores, embora
  o carregamento atual defina somente 0, 1 e 2. Confirmar o conjunto pretendido.
- Há textos legados sobre classificação binária e CART incompatíveis com
  o código atual de RF com três classes.

Essas pendências foram registradas, sem alterar o notebook ou o módulo.
Não há conclusão sobre suporte real a probabilidades, resultados numéricos,
autenticação ou acesso aos assets nesta inspeção.

## Encaminhamento ao step 2

Definir a assinatura de `Visualizer.plot_random_forest_classification` usando
as predições já existentes, lista de preditores, propriedades `landcover` e
`classification`, nomes de classes opcionais, projeção PCA/duas bandas,
limite de amostras, seed, caminho PNG e `show=False`. Preservar os helpers de
treino/avaliação; distinguir métricas completas das métricas do subconjunto
plotado. A assinatura final e sua implementação pertencem às próximas etapas.
