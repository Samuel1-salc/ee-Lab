# Análise do gráfico — Random Forest no Google Earth Engine

O gráfico apresenta o resultado de uma classificação supervisionada com Random Forest, aplicada a três classes de cobertura da superfície terrestre: Floresta, Agricultura e Água.

A principal conclusão é que o classificador apresentou um desempenho muito alto, com 99,60% de acurácia, e as amostras das três classes aparecem bem separadas na projeção bidimensional.

Entretanto, há uma distinção importante: o gráfico mostra a organização das amostras por PCA, não as fronteiras de decisão reais do Random Forest.

## 1. Interpretação dos indicadores

Amostras avaliadas

# 3.000

Acurácia

# 99,60%

Índice Kappa

# 0,994

Proporção de classificações corretas

99,60%

2.988 acertos

12 erros

Quantidades calculadas a partir da acurácia exibida, supondo que ela foi calculada exatamente sobre as 3.000 amostras.

### Acurácia de 99,60%

A acurácia mede a proporção de classificações corretas:

\\[ Accuracy=\frac{\text{Predições corretas}}{\text{Total de amostras}} \\]

Assim:

\\[ 3000 \times 0{,}996 = 2988 \\]

Portanto, o resultado equivale a aproximadamente 2.988 amostras classificadas corretamente e 12 incorretamente.

Isso significa que, para cada 1.000 amostras avaliadas, cerca de 996 receberam o rótulo correto.

### Índice Kappa de 0,994

O Kappa mede a concordância entre a classificação e os rótulos de referência, corrigindo a parcela de concordância esperada ao acaso.

\\[ \kappa=\frac{P_o-P_e}{1-P_e} \\]

Onde:

- \\(P_o\\) é a concordância observada.
- \\(P_e\\) é a concordância esperada ao acaso.

Um valor de 0,994, muito próximo de 1, representa concordância extremamente elevada.

Acurácia e Kappa, portanto, apontam na mesma direção: o classificador reproduziu muito bem as classes de referência no conjunto avaliado.

## 2. O significado dos eixos PC1 e PC2

O gráfico utiliza PCA (Principal Component Analysis), uma técnica de redução de dimensionalidade baseada em álgebra linear.

Imagine que cada amostra do Earth Engine tenha várias informações espectrais:

\\[ X_i=[B2,B3,B4,B8,B11,B12,NDVI,NDWI,\ldots] \\]

Cada banda ou índice representa uma dimensão do espaço de atributos.

Como é impossível representar diretamente muitas dimensões em uma figura plana, o PCA combina linearmente esses atributos em novos eixos.

| Componente         | Variância explicada | Interpretação                                               |
| ------------------ | ------------------- | ----------------------------------------------------------- |
| PC1 (horizontal)   | 45,9%               | Principal direção de variação dos dados                     |
| PC2 (vertical)     | 18,8%               | Segunda principal direção de variação, ortogonal à primeira |
| Demais componentes | 35,3%               | Informação não representada neste gráfico                   |

Variância explicada pelo PCA

Total: 100%

PC1 45,9%

PC2 18,8%

Não exibida 35,3%

Os dois eixos representam, juntos, 64,7% da variância total.

Isso é suficiente para visualizar uma estrutura bastante clara, mas significa que 35,3% da variabilidade está em outras dimensões.

Atenção: PC1 e PC2 não são latitude, longitude nem bandas individuais do satélite. São combinações matemáticas dos atributos originais. Sem os coeficientes do PCA (loadings), não é possível dizer quais bandas mais influenciaram cada eixo.

## 3. Análise individual das três classes

Floresta — agrupamento superior

Região aproximada: PC1 entre −5 e +4; PC2 entre +2,5 e +8.

As amostras de floresta formam uma nuvem relativamente compacta, concentrada perto de PC1 = 0 e PC2 = 6. Há alguns pontos dispersos nas extremidades. A concentração sugere que grande parte das amostras apresenta características espectrais semelhantes, após a transformação pelo PCA.

Agricultura — agrupamento à direita

Região aproximada: PC1 entre +4,5 e +16; PC2 entre 0 e −11.

As amostras agrícolas apresentam uma distribuição alongada, com tendência descendente: valores maiores de PC1 aparecem associados a valores menores de PC2. Isso revela variação interna considerável, que pode ser compatível com diferenças entre cultivos, estágios fenológicos ou condições do solo. O gráfico, isoladamente, não identifica qual fator é responsável.

Água — agrupamento inferior esquerdo

Região aproximada: PC1 entre −14 e +1,5; PC2 entre +2 e −12,5.

A classe água possui uma nuvem mais espalhada, com um núcleo denso próximo de PC1 = −9 e PC2 = −3. Sua dispersão pode refletir diferentes características espectrais entre amostras, como turbidez, sedimentos ou mistura de pixels. Essas são hipóteses físicas plausíveis, não conclusões comprovadas pelo PCA.

### O que a separação entre os grupos revela?

O aspecto mais relevante é que os três agrupamentos estão visualmente bem separados.

A floresta aparece na região superior; a agricultura, à direita; a água, predominantemente à esquerda e abaixo.

Isso sugere que os atributos utilizados possuem bom poder discriminativo para essas três classes.

No contexto de sensoriamento remoto, essa separação é fisicamente plausível porque superfícies distintas interagem de maneiras diferentes com a radiação eletromagnética. A vegetação, por exemplo, apresenta resposta característica no infravermelho próximo, enquanto corpos d'água frequentemente exibem baixa reflectância nessa faixa.

Entretanto, não podemos identificar quais bandas produziram a separação observada sem examinar os atributos de entrada e os componentes do PCA.

## 4. O significado dos círculos e dos X

A legenda utiliza duas formas de representar o desempenho:

- Círculo (●): amostra classificada corretamente.
- X (×): amostra classificada incorretamente.

A cor representa a classe real da amostra, inclusive quando ela foi classificada incorretamente.

Por exemplo, um X vermelho significa que aquela amostra pertence à classe Água, mas o classificador previu outra classe. O gráfico não informa qual classe foi prevista.

Os erros aparecem relativamente isolados e em pequeno número, coerentemente com a acurácia de 99,60%.

Um detalhe interessante: alguns X aparecem próximos de agrupamentos de outras classes, mas outros estão dentro ou próximos de suas próprias nuvens. Isso ocorre porque a visualização reduz os dados a duas dimensões, enquanto o Random Forest pode tomar decisões considerando muitos atributos.

Portanto, a distância entre pontos no PCA não determina, por si só, se o Random Forest acertará ou errará.

## 5. O que o gráfico comprova e o que ainda precisa ser validado?

| Observação                        | Interpretação                                                      |
| --------------------------------- | ------------------------------------------------------------------ |
| Acurácia 99,60%                   | Excelente desempenho no conjunto avaliado                          |
| Kappa 0,994                       | Concordância muito elevada com os rótulos de referência            |
| Três grupos bem separados         | Boa separabilidade na projeção dos atributos                       |
| Poucos X visíveis                 | Pequeno número de erros em relação ao total                        |
| Agricultura e água mais dispersas | Maior variabilidade interna aparente nessas classes                |
| PCA explica 64,7%                 | A projeção preserva parte importante, mas não toda a variabilidade |

Há três cuidados metodológicos importantes.

Primeiro: a acurácia elevada não garante desempenho igualmente alto em toda a área geográfica. Ela descreve o conjunto de validação. Se as amostras de treino e validação vieram de pixels espacialmente muito próximos, por exemplo, o resultado pode ser otimista por causa da autocorrelação espacial.

Segundo: não sabemos o desempenho individual de cada classe. Um modelo pode alcançar 99,60% de acurácia global e ainda apresentar erros concentrados em uma categoria. Seria necessário consultar a matriz de confusão e os valores de precisão, recall e F1-score por classe.

Terceiro: o gráfico não é uma representação geográfica. Dois pontos próximos nele possuem coordenadas PCA semelhantes, mas podem ter sido coletados em localidades muito distantes na superfície terrestre.

## 6. Minha avaliação técnica para o seu visualizer

Para seu projeto no Google Earth Engine, eu consideraria esse gráfico um bom diagnóstico visual do espaço de atributos e da classificação, mas não o utilizaria sozinho como prova de qualidade do modelo.

A combinação mais informativa seria:

1. Projeção PCA: mostra a organização das amostras e evidencia acertos e erros.
2. Matriz de confusão: informa quais classes estão sendo confundidas.
3. Precisão, recall e F1 por classe: revelam se alguma classe apresenta desempenho inferior.
4. Importância das variáveis: ajuda a entender quais bandas e índices espectrais contribuíram para o Random Forest.
5. Mapa geográfico de erros: mostra onde as classificações incorretas se concentram espacialmente.

### Conclusão

O modelo apresenta uma classificação aparentemente muito consistente: 3.000 amostras avaliadas, aproximadamente 2.988 classificações corretas, 12 erros e concordância Kappa de 0,994.

A separação visual entre Floresta, Agricultura e Água reforça que os atributos utilizados conseguem distinguir bem as três coberturas no conjunto analisado.

A principal informação que falta não é outra projeção PCA: é a matriz de confusão e a validação espacial independente. São esses resultados que permitirão determinar se o desempenho de 99,60% se traduz em um mapeamento territorial realmente confiável.