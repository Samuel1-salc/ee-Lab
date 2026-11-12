No seu notebook, a forma mais simples seria criar uma faixa de exclusão em torno dos polígonos de validação e retirar do treino os polígonos que a intersectam.

Após definir poligonos_treino e poligonos_validacao, antes da rasterização:

# Exemplo inicial; a distância deve ser escolhida para a área estudada.
DISTANCIA_MINIMA_M = 300

faixa_validacao = (
    poligonos_validacao
    .geometry()
    .buffer(DISTANCIA_MINIMA_M)
)

poligonos_treino = poligonos_treino.map(
    lambda feature: feature.set(
        "_proximo_validacao",
        feature.geometry().intersects(faixa_validacao, 1),
    )
).filter(ee.Filter.eq("_proximo_validacao", False))

O restante do fluxo permanece: rasterizar → amostrar → treinar → avaliar. As verificações de quantidade por classe devem ocorrer depois dessa exclusão.

Os 300 m são apenas ilustrativos. Uma distância maior pode remover muitos polígonos e deixar classes sem treinamento. Para avaliar generalização entre regiões, outra opção é reservar blocos geográficos inteiros para validação.
