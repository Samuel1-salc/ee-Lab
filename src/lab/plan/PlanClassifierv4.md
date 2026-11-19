# Criação do classifier v4

-- O que eu quero é agora inserir a classe de pastagem e melhorar a classe de area Urbana. Utilizando para melhorar a identificação de pastagem amostras estastiticas criando WIDE table com modis (EVI)

-- Agora as classes de plantação (agricultura) de floresta (reserva e cerrado) de água foram coletadas utilizando landsat 8. porém ao quero jogar as bandas espectrais para esses poligno (crus) de amostra utilizando o feature space e suas reduções utilizando o Featurespace do landsat 8, criado no repositório `repository_ee`

-- 1 primeiro quero utilizar a mesma estrutura de fases até a classificação do modelo e validação do classification-v3.ipynb

-- 2 adicionar as labels no caso uma amostra já coom bandas evi que seria a de pastagem. e adiciona-las ao processo de classificação junto com as outras labels (ainda cruas sem BANDAS apenas polignos classificados como água, agricultura e etc).

-- 3 utilizar o mesmo random forest

-- 4 utilizar o processo de distancia dos pontos

-- 5 utilizar a area de estudo já criada no EE, vou passar todos os links dos assets aqui

-- 6 utilize algum metodo de exportação da imagem gerada pelo modelo classificado no EE do repository_ee

-- ao final tambem crie igual está no classificador base desse projeto 9 o (calssificador v3 ) o metodo visualizer para criação do gráfico de resultado de clusterização

-- para o gráfico de clusterização do vizualizer é calculado PCA , para isso analize o PCA do metodo visualizer e compare o PCA que está na pasta src/lab/tutorial/PCA , para isso veriffique se eles tem como objetivo de fazer a mesma coisa que seria clusterização. Caso sim me fale (essa vai ser o ultimo step a ser analisado)


## LINK DAS LABELS
area de estudo = projects/lateral-spirit-514212-j0/assets/Amostras_spatiov1_2025
projects/lateral-spirit-514212-j0/assets/tocantins_2025_AGRICULTURA
projects/lateral-spirit-514212-j0/assets/tocantins_2025_AGUA
projects/lateral-spirit-514212-j0/assets/tocantins_2025_RESERVA_FLORESTAL
projects/lateral-spirit-514212-j0/assets/tocantins_2025_RESERVA_URBANA
projects/lateral-spirit-514212-j0/assets/Amostras_PASTAGEM_WIDE_2025