# Modelagem Harmônica do Landsat 8 para Análise Fenológica e Classificação de Pastagens

## 1. Objetivo geral

O script **Landsat 8 Harmonic Modeling** busca representar matematicamente a **fenologia da vegetação** — suas variações sazonais ao longo do tempo — a partir de séries temporais do **Índice de Vegetação por Diferença Normalizada (NDVI)**.

Em vez de analisar uma única imagem, o procedimento ajusta um modelo temporal a várias observações e permite investigar **quando** a vegetação atinge seu pico, **quanto** seu vigor varia e **qual** é seu nível médio de NDVI.

**Aplicação central:** gerar atributos temporais úteis para visualizar padrões sazonais e alimentar classificadores supervisionados de uso e cobertura da terra, incluindo a distinção entre pastagens, florestas e agricultura.

## 2. Fundamentos da regressão harmônica

A regressão harmônica aproxima a série temporal por uma combinação de funções senoidais. Para um ciclo anual simples:

$$
\widehat{NDVI}(t) = \beta_0 + \beta_t t + a\cos(2\pi t) + b\sin(2\pi t)
$$

Em que:

- $t$ é o tempo em anos, definido a partir de uma origem temporal consistente;
- $\beta_0$ é o intercepto;
- $\beta_t$ é a tendência linear, quando incluída;
- $a$ e $b$ são coeficientes harmônicos;
- $\widehat{NDVI}(t)$ é o NDVI estimado.

A **amplitude** do ciclo é $A=\sqrt{a^2+b^2}$. A **fase** pode ser representada por $\phi=\operatorname{atan2}(b,a)$ na convenção acima, pois $a\cos(\omega t)+b\sin(\omega t)=A\cos(\omega t-\phi)$. O pico anual ocorre quando $2\pi t=\phi\pmod{2\pi}$, **desde que** o ciclo seja bem descrito por um único harmônico e a tendência não altere substancialmente a localização do máximo.

> **Atenção:** a interpretação da fase depende da ordem dos coeficientes, da convenção trigonométrica e da origem do tempo usadas no script. A banda `constant` é o intercepto, **não necessariamente a média temporal** quando há tendência ou quando o tempo não está centrado.

### 2.1. Modelagem dos ciclos de crescimento

A vegetação pode responder de modo sazonal às chuvas, à temperatura e ao manejo. O ajuste harmônico descreve uma componente periódica dessas mudanças, reduzindo a dependência de observações isoladas.

### 2.2. Ruído e lacunas temporais

O modelo produz a série estimada (`fitted`), inclusive em datas sem observações válidas. Isso **não equivale** a recuperar os valores reais perdidos nem a remover automaticamente todos os efeitos atmosféricos: o resultado depende de máscaras de nuvens, correção radiométrica, qualidade dos dados e adequação do modelo.

### 2.3. Mapa de sazonalidade em HSV

Uma visualização possível codifica três atributos em **HSV (Hue, Saturation, Value)**, posteriormente convertido para RGB:

| Canal | Atributo | Interpretação |
|---|---|---|
| **Hue (matiz)** | Fase | Época relativa do pico sazonal do NDVI |
| **Saturation (saturação)** | Amplitude | Intensidade da oscilação sazonal |
| **Value (brilho)** | Nível médio/intercepto | Vigor médio aproximado, conforme a parametrização |

As cores **dependem da normalização e das escalas escolhidas**. O HSV é principalmente uma representação visual; para classificação, é preferível usar os atributos numéricos originais.

## 3. Pastagens e sua assinatura fenológica

Pastagens frequentemente respondem à alternância entre períodos secos e chuvosos, mas **não possuem uma assinatura universal**. Tipo de gramínea, solo, precipitação, irrigação, pastejo, fogo e degradação modificam a série temporal.

### 3.1. Interpretação dos atributos

| Atributo | Possível comportamento em pastagens | Ressalva |
|---|---|---|
| **Amplitude** | Pode ser elevada em pastagens sazonalmente dependentes da chuva | Agricultura e vegetação natural sazonal também podem ter amplitude elevada |
| **Fase** | Pode acompanhar a estação chuvosa | Manejo, irrigação e calendário agrícola podem deslocar o pico |
| **NDVI médio** | Pode ser intermediário entre solo exposto e floresta densa | Há ampla sobreposição entre classes |
| **Tendência** | Pode indicar mudança persistente no vigor | Não prova degradação sem evidências adicionais |

### 3.2. Comparação com outras coberturas

- **Florestas perenes:** frequentemente mantêm NDVI relativamente alto e amplitude menor, mas há exceções.
- **Culturas anuais:** podem exibir ciclos intensos, quedas após colheita e múltiplas safras.
- **Pastagens:** podem apresentar variação associada às chuvas, ao manejo e à pressão de pastejo.
- **Pastagens irrigadas:** podem manter NDVI mais estável e se confundir com outras coberturas perenes.

**Conclusão:** o mapa harmônico ajuda a formular hipóteses sobre pastagens, mas **não identifica a classe nem diagnostica degradação sozinho**. É necessário validar com amostras de referência e, idealmente, outros atributos espectrais e ambientais.

## 4. Utilização dos coeficientes na classificação supervisionada

A abordagem consiste em construir uma **imagem multibanda de preditores**, extrair seus valores em amostras rotuladas, treinar um classificador e aplicar o modelo à área de estudo.

### 4.1. Montar a pilha de atributos

Exemplo para o **Google Earth Engine (JavaScript)**, supondo que `harmonicTrendCoefficients`, `magnitude` e `phase` já tenham sido calculados e que as bandas harmônicas sejam denominadas `sin_1` e `cos_1`:

```javascript
var preditores = ee.Image.cat([
  harmonicTrendCoefficients.select('constant'),
  magnitude.rename('magnitude'),
  phase.rename('phase'),
  harmonicTrendCoefficients.select('sin_1'),
  harmonicTrendCoefficients.select('cos_1')
]);
```

> **Nota:** os nomes das bandas e a existência de `phase` e `magnitude` dependem da implementação concreta do script. Se houver uma banda de tendência, ela também pode ser incluída. Coeficientes seno/cosseno podem ser preferíveis à fase isolada, porque evitam a descontinuidade angular entre o fim e o início do ciclo.

### 4.2. Extrair amostras rotuladas

A coleção `suas_amostras` deve conter geometrias e um atributo `class`, por exemplo: **0 = floresta; 1 = pastagem; 2 = agricultura**.

```javascript
var training = preditores.sampleRegions({
  collection: suas_amostras,
  properties: ['class'],
  scale: 30,
  geometries: false
});
```

Amostras devem representar adequadamente cada classe e sua variabilidade espacial e temporal. Pixels mascarados podem ser excluídos na amostragem.

### 4.3. Treinar o Random Forest

```javascript
var classifier = ee.Classifier.smileRandomForest(100).train({
  features: training,
  classProperty: 'class',
  inputProperties: preditores.bandNames()
});

var classified = preditores.classify(classifier);

Map.addLayer(
  classified,
  {min: 0, max: 2, palette: ['006400', 'FFD700', 'FF8C00']},
  'Classificação Harmônica'
);
```

Esse exemplo demonstra o treinamento e a inferência, **não uma avaliação de acurácia**.

### 4.4. Validar antes de interpretar

1. Separar amostras de treino e teste, preferencialmente com **separação espacial** para reduzir vazamento de informação entre pixels vizinhos.
2. Construir uma **matriz de confusão** com dados de teste independentes.
3. Calcular métricas por classe, como **precisão, revocação e F1-score**, além da acurácia global.
4. Inspecionar especialmente confusões entre **pastagem, agricultura e vegetação natural sazonal**.
5. Verificar se o intervalo temporal do modelo corresponde ao período representado pelos rótulos.

## 5. Por que utilizar atributos harmônicos?

| Benefício | Explicação |
|---|---|
| **Informação temporal** | Diferencia pixels com NDVI semelhante em uma data, mas ciclos sazonais distintos |
| **Menor dependência de uma cena** | Integra múltiplas observações em vez de depender de uma única imagem |
| **Atributos interpretáveis** | Amplitude, fase e tendência têm significado fenológico |
| **Integração com ML** | Os coeficientes podem alimentar Random Forest, SVM e outros classificadores |

**Limite importante:** uma série de vários anos pode suavizar mudanças reais de uso da terra. Para mapear um ano específico, ajuste a janela temporal à pergunta de pesquisa e avalie mudanças de cobertura.

## 6. Possíveis melhorias

- **Bandas espectrais e índices:** NDVI, EVI, NDWI e bandas do Landsat podem complementar os harmônicos.
- **Harmônicos adicionais:** podem representar dois ciclos agrícolas anuais, quando os dados suportarem esse ajuste.
- **Textura e contexto espacial:** métricas de vizinhança ajudam a caracterizar padrões, mas não substituem validação.
- **Sentinel-1:** dados de radar podem fornecer informação complementar em regiões com cobertura de nuvens.
- **Dados auxiliares:** precipitação, relevo e histórico de uso podem ajudar a separar respostas fenológicas semelhantes.

## 7. Síntese do fluxo

```text
Landsat 8 (série temporal)
          |
          v
Máscaras de qualidade + cálculo do NDVI
          |
          v
Regressão harmônica por pixel
          |
          +--> Visualização HSV -> RGB
          |
          v
Coeficientes e atributos derivados
          |
          v
Amostras rotuladas + validação espacial
          |
          v
Random Forest / SVM
          |
          v
Mapa de classes + métricas de desempenho
```

## 8. Conclusão

A modelagem harmônica transforma observações de NDVI em descritores do **comportamento sazonal** de cada pixel. Esses descritores podem melhorar a separação entre classes de uso e cobertura da terra, inclusive pastagens, quando combinados com amostras confiáveis, variáveis complementares e validação rigorosa.

O principal ganho não é uma cor específica no mapa HSV, mas a possibilidade de usar **a dinâmica temporal da vegetação como informação quantitativa para classificação**.
