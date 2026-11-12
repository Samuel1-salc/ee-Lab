# Step 2 — Contrato e fluxo do Visualizer

Proposta referente a `planVisualizer.md#step-2`, baseada na inspeção registrada
em `visualizer-discovery.md`. O MVP da etapa 3 está implementado em
`repository_ee.py`, com a assinatura abaixo. A integração real EE e a
renderização ainda devem ser verificadas no ambiente com as dependências.

## Assinatura atual

Atualização solicitada pelo usuário: receber o resultado completo de
`Models.validation_metrics` e reutilizar suas métricas GEE, sem recalculá-las
localmente. Essa decisão substitui a proposta inicial de métricas do subconjunto.

Adicionar um método estático à classe **`Visualizer` existente** em
`src/lab/base/repository_ee.py`, acompanhando os helpers do módulo e evitando
construtor ou configuração global para uma única operação:

```python
@staticmethod
def plot_random_forest_classification(
    validation_metrics: Mapping[str, Any],
    feature_columns: Sequence[str] | ee.List,
    *,
    label_property: str = "class_id",
    prediction_property: str = "classification",
    class_names: Mapping[int, str] | None = None,
    projection: str = "pca",
    plot_bands: tuple[str, str] | None = None,
    standardize: bool = False,
    output_path: str | Path = "plots/random-forest-classification.png",
    max_samples: int = 3000,
    seed: int = 0,
    figsize: tuple[float, float] = (10, 8),
    dpi: int = 150,
    show: bool = False,
) -> dict[str, Any]:
    ...
```

`Path` será importado de `pathlib`. Os defaults são decisões desta proposta,
não configurações já existentes no repositório. O rótulo padrão `class_id`
acompanha `Models`; no notebook em questão deve ser informado `landcover`.

## Contrato de entrada

- `validation_metrics`: dicionário completo retornado por
  `Models.validation_metrics`, incluindo `predictions` e métricas GEE.
  O chamador informa os mesmos campos de rótulo e predição usados na avaliação.
- `feature_columns`: nomes explícitos dos preditores, aceitando a `ee.List`
  `bandas_preditoras` do notebook. Materializar essa pequena lista, quando
  necessário, sem consultar pixels da imagem.
- `class_names`: mapa opcional de código inteiro para nome legível. Códigos
  ausentes no mapa aparecem como o próprio código. Não assumir classes consecutivas.
- `projection`: somente `pca` ou `bands`. Em `bands`, exigir dois nomes distintos
  em `plot_bands`, ambos pertencentes aos preditores. Em `pca`, rejeitar
  `plot_bands` para evitar configuração ignorada.
- `standardize`: padronização opcional antes do PCA, desativada por padrão
  para acompanhar a referência simples. Rejeitar `True` no modo `bands`, que
  deve preservar os valores dos eixos originais.
- `max_samples`: inteiro positivo, padrão 3000 e teto proposto de 10000.
  Volumes maiores exigem uma estratégia explícita futura, não download automático.
- `output_path`: arquivo `.png`, relativo ao diretório atual ou absoluto.
  Criar diretórios pais com `Path.mkdir(parents=True, exist_ok=True)`.
  Chamadas com o mesmo caminho substituem a figura anterior; o chamador pode
  fornecer nomes distintos. Validar tamanho de figura e DPI positivos.

Rejeitar coleção vazia, nomes duplicados de preditores e inclusão do rótulo
ou da predição na projeção. Probabilidades também não são preditores: a lista
deve vir das bandas do treinamento, sem colunas diagnósticas acrescentadas.
Rejeitar colunas ausentes, valores nulos, não numéricos ou não finitos no
subconjunto extraído, com mensagem indicando o campo. Rótulos e predições
devem ser códigos inteiros. Não descartar linhas silenciosamente.
PCA exige ao menos duas amostras, dois preditores e variância total não nula.
Colunas constantes com padronização devem ser tratadas sem divisão por zero.

## Fluxo e responsabilidades

```text
metricas_validacao + bandas_preditoras
    → validar configuração e resolver nomes dos preditores
    → ordenar pseudoaleatoriamente com seed e limitar no servidor
    → selecionar somente atributos necessários e remover geometria
    → materializar uma única tabela limitada
    → validar atributos, rótulos e predições
    → materializar métricas GEE recebidas e projetar os preditores
    → renderizar scatter, salvar PNG e fechar figura
    → retornar caminho, métricas, contagens e avisos
```

A seleção será sem reposição e sem balanceamento adicional por classe.
A repetibilidade depende de manter a mesma coleção e identificadores EE;
não prometer a mesma seleção após reconstruções que alterem esses identificadores.
Consultar a contagem total como agregado pequeno para informar se houve corte.
O limite deve ser aplicado antes da conversão EE→pandas, nunca depois do download.
Rótulos e predições permanecem na mesma linha, sem duas consultas a serem alinhadas.

O PCA é ajustado apenas nos preditores do subconjunto plotado para uma
visualização descritiva; não alimenta o classificador ou uma avaliação preditiva.
Não representa fronteira de decisão, mapa geográfico ou clustering.
O modo `bands` usa nomes reais como `nir`/`red`, sem atribuir unidades não verificadas.

Separar helpers privados pequenos dentro de `Visualizer` para extração da
tabela, validação, projeção, métricas e renderização/salvamento. Não criar
hierarquia de classes, adaptador de treinamento ou novo pipeline de classificação.
Reutilizar pandas e o padrão de imports locais dos helpers de plotagem;
NumPy/Matplotlib e PCA do scikit-learn são suficientes, com PCA importado apenas
quando solicitado. Nenhuma inicialização EE ou exportação ocorre na importação.

## Métricas e desenho

Reutilizar matriz, ordem das classes, acurácia, kappa e acurácias do produtor
e consumidor fornecidas pelo GEE via `Models.validation_metrics`.
O gráfico mostra acurácia e kappa como **métricas da validação completa**,
mesmo quando `max_samples` limita os pontos. Não há cálculo local de F1,
matriz ou acurácia; a comparação de rótulos serve apenas aos marcadores.
Manter checagens básicas de configuração e dados para permitir renderização,
sem validação científica adicional ou novo treinamento.

Usar cores por classe verdadeira e marcadores `o`/`x` para acerto/erro,
legenda dinâmica, grade e caixa de métricas. Identificar validação, seed,
quantidade plotada/total e número de classes verdadeiras representadas.
PCA mostra variância explicada nos eixos. Sempre salvar PNG; `show=True`
também exibe a figura. Fechar a figura inclusive quando ocorrer erro ao salvar.

## Retorno proposto

Manter o padrão de dicionários do módulo, com valores locais:

| Chave | Conteúdo |
|---|---|
| `output_path` | `Path` do PNG salvo |
| `metrics` | `scope="full_validation"`, `class_order`, `confusion_matrix`, `accuracy`, `kappa`, `producers_accuracy`, `consumers_accuracy` |
| `sample_counts` | `available` e `plotted` |
| `projection` | `pca` ou `bands` |
| `feature_columns` | Lista efetiva dos preditores |
| `plot_bands` | Duas bandas no modo `bands`; `None` no PCA |
| `explained_variance_ratio` | Dois valores no PCA; `None` no modo `bands` |
| `standardized` | Se a padronização foi aplicada |
| `seed` | Seed da seleção para visualização |
| `warnings` | Lista de avisos, incluindo corte de amostras e classes não representadas, quando detectáveis |

Os arrays de produtor/consumidor preservam o formato GEE e seguem `class_order`.
A matriz usa listas de listas de inteiros. Não retornar figura aberta,
coleção EE ou tabela completa no resultado.

## Chamada prevista no notebook

Adicionar após obter `metricas_validacao`, quando o método estiver implementado
e as pendências do notebook identificadas no step 1 estiverem resolvidas:

```python
from repository_ee import Visualizer

resultado_visualizacao = Visualizer.plot_random_forest_classification(
    validation_metrics=metricas_validacao,
    feature_columns=bandas_preditoras,
    label_property=PROPRIEDADE_CLASSE,
    prediction_property="classification",
    class_names={0: "Floresta", 1: "Agricultura", 2: "Água"},
    projection="pca",
    output_path="plots/random-forest-validation.png",
    max_samples=3000,
    seed=SEED,
    show=False,
)
```

Para duas bandas, usar `projection="bands"` e `plot_bands=("nir", "red")`,
após confirmar esses nomes em `bandas_preditoras`. O mapa de nomes acima reflete
as três classes carregadas pelo notebook atual; não inclui urbano inexistente.

## Critérios de aceite da etapa 2 e próximos passos

1. Componentes reais e dados reutilizados identificados: `Visualizer`,
   `Models.validation_metrics`, suas `predictions` e `bandas_preditoras`.
2. Entradas, retorno, limite, escopo das métricas e fluxo definidos acima.
3. Treinamento, amostragem e API existente preservados: esta etapa adiciona
   somente a proposta, sem alterar o módulo ou notebook.

Na etapa 3, implementar o MVP e verificar sintaxe e uma pequena renderização
local com dados controlados. Na etapa 4, validar a chamada EE real e a integração
do notebook, após resolver as inconsistências registradas na descoberta.
Nas etapas 5 e 6, definir separadamente a extensão opcional de probabilidades
e diagnósticos: suporte, ordem das classes e identidade das amostras precisam
ser comprovados antes de ampliar a assinatura. A proposta não afirma que isso
já foi verificado e não exige essa extensão para o MVP.
