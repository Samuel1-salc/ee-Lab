# Plan-Orchestrate Result

**Plano** `src/lab/plan/PlanClassifierv4.md`  
**Escopo** `all` · **Etapas** 8 · **Emitidas** 7 · **Bloqueadas** 1

| # | Etapa | Tags | Comando | Status |
|---|---|---|---|---|
| 1 | Criar o notebook v4 a partir do v3 | `impl` | `/orch-add-feature` | Emitida |
| 2 | Integrar pastagem e melhorar a classe urbana | `change`, `impl` | `/orch-change-feature` | Emitida |
| 3 | Reutilizar o Random Forest | `impl` | `/orch-add-feature` | Emitida |
| 4 | Integrar a separação por distância | `impl` | `/orch-add-feature` | Emitida |
| 5 | Configurar a área de estudo e os assets | `change` | `/orch-change-feature` | Emitida |
| 6 | Preparar a exportação do mapa classificado | `impl` | `/orch-add-feature` | Emitida |
| 7 | Integrar o gráfico do visualizador | `impl` | `/orch-add-feature` | Emitida |
| 8 | Comparar o PCA do visualizador com o tutorial | `review` | `/code-review` | Bloqueada |

### Etapa 1 — Criar o notebook v4

Cria o notebook com a sequência de fases do v3, da preparação dos dados à classificação e à avaliação do modelo.

### Etapa 2 — Integrar pastagem e melhorar a classe urbana

Altera as classes e a preparação das amostras. A decisão técnica desta etapa é definir **uma unidade de classificação e um conjunto comum de preditores**. Os polígonos rotulados precisam ter as mesmas entradas no treino, e a aplicação à imagem exige bandas correspondentes. O plano pede melhorar a classe urbana, mas não define uma meta de desempenho.

### Etapa 3 — Reutilizar o Random Forest

Leva para o v4 o classificador e os parâmetros definidos no v3, usando as classes e os preditores preparados para a nova versão.

### Etapa 4 — Integrar a separação por distância

Reaproveita o processo do projeto para separar espacialmente as amostras de treino e validação.

### Etapa 5 — Configurar a área de estudo e os assets

Use os seguintes IDs em uma célula de configuração de `classification-v4.ipynb`. A geometria da área de estudo vem de `projects/lateral-spirit-514212-j0/assets/Amostras_spatiov1_2025`.

| Entrada | Asset do Earth Engine |
|---|---|
| Área de estudo | `projects/lateral-spirit-514212-j0/assets/Amostras_spatiov1_2025` |
| Agricultura | `projects/lateral-spirit-514212-j0/assets/tocantins_2025_AGRICULTURA` |
| Água | `projects/lateral-spirit-514212-j0/assets/tocantins_2025_AGUA` |
| Reserva florestal | `projects/lateral-spirit-514212-j0/assets/tocantins_2025_RESERVA_FLORESTAL` |
| Área urbana | `projects/lateral-spirit-514212-j0/assets/tocantins_2025_RESERVA_URBANA` |
| Pastagem (Wide Table de EVI) | `projects/lateral-spirit-514212-j0/assets/Amostras_PASTAGEM_WIDE_2025` |

### Etapa 6 — Preparar a exportação do mapa classificado

Usa um método de `Exports` para criar a tarefa de exportação da imagem classificada para um asset do Earth Engine. O ID do asset de saída fica configurável.

### Etapa 7 — Integrar o gráfico do visualizador

Reaproveita o visualizador do v3 para mostrar a distribuição das amostras do v4 no espaço de componentes principais.

### Etapa 8 — Comparar as implementações de PCA

A comparação deve verificar se o PCA do visualizador e o de `src/lab/tutorial/PCA` têm o mesmo objetivo, quais dados recebem e se existe um algoritmo de agrupamento após a projeção. `/code-review` aceita um número ou URL de PR, ou pode ser usado sem argumentos. Esse formato não carrega o escopo da comparação.

```text
BLOCKED — /code-review cannot carry plan scope; run manually if wanted: /code-review
```

### Batch execution

Os comandos abaixo foram preparados para copiar. Nenhum foi executado.

```text
/orch-add-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-1] Crie src/lab/base/classification-v4.ipynb a partir de classification-v3.ipynb e reproduza a sequência de fases até a classificação e a avaliação do modelo. Acceptance: o v4 fica em um notebook próprio; as fases de preparação, classificação e avaliação seguem a estrutura do v3."
/orch-change-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-2] No classification-v4.ipynb, adicione pastagem e revise a preparação da classe urbana. Use a Wide Table de EVI MODIS Amostras_PASTAGEM_WIDE_2025 e derive preditores dos polígonos de água, agricultura, floresta, Cerrado e área urbana com o feature space Landsat 8 de repository_ee. Acceptance: as classes têm rótulos explícitos; as amostras compartilham um esquema de preditores; a imagem de inferência fornece bandas equivalentes na unidade de classificação escolhida."
/orch-add-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-3] Integre ao classification-v4.ipynb o mesmo Random Forest de classification-v3.ipynb, usando os rótulos e preditores preparados para o v4. Acceptance: a configuração do Random Forest é reaproveitada do v3; o treinamento recebe explicitamente a propriedade de classe e a lista de preditores."
/orch-add-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-4] Integre ao classification-v4.ipynb o processo de distância entre pontos já usado no projeto para separar as amostras de treinamento e validação. Acceptance: o cálculo usa o critério de distância existente; os conjuntos resultantes alimentam respectivamente o treinamento e a avaliação."
/orch-change-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-5] Configure classification-v4.ipynb com os assets do Earth Engine sob projects/lateral-spirit-514212-j0/assets/: área de estudo=Amostras_spatiov1_2025; agricultura=tocantins_2025_AGRICULTURA; água=tocantins_2025_AGUA; floresta=tocantins_2025_RESERVA_FLORESTAL; urbana=tocantins_2025_RESERVA_URBANA; pastagem (Wide Table EVI)=Amostras_PASTAGEM_WIDE_2025. Acceptance: a configuração contém os seis IDs completos; a geometria de estudo vem do asset indicado; cada fonte fica associada à classe correspondente."
/orch-add-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-6] Prepare a exportação da imagem classificada de classification-v4.ipynb para um asset do Earth Engine usando um método de Exports em repository_ee. Acceptance: a tarefa usa a imagem classificada e a geometria da área de estudo; o ID de destino fica configurável; a chamada start() fica comentada para início manual."
/orch-add-feature "[Plan: src/lab/plan/PlanClassifierv4.md#step-7] Integre ao classification-v4.ipynb o visualizador usado no v3 para gerar o gráfico das amostras no espaço PCA. Acceptance: o gráfico usa os preditores do v4; as classes exibidas correspondem aos rótulos configurados; o notebook reaproveita o método visualizer do projeto."
```