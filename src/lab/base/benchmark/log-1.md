Polígonos de treinamento: {'0': 11, '1': 45, '2': 20}
Polígonos de validação: {'0': 3, '1': 20, '2': 6}
+
-
Draw a polyline
Draw a polygon
Draw a rectangle
Draw a marker
Edit layers
Delete layers
Measure
30 km
10 mi
ipyleaflet | © OpenStreetMap contributors, Google Earth Engine
Amostras de treinamento: {'0': 800, '1': 800, '2': 800}
Amostras de validação: {'0': 800, '1': 800, '2': 800}
Object (5 properties)
classes: [0, 1, 2]
dot:digraph DecisionTree { node [shape=box, style="filled, rounded", color="black", fontname=helvetica]; edge [fontname=helvetica]; 0 [label=<mndwi &le; -0.3824<br/>score = 0.3315>, fillcolor="#00000000"]; 1 [label=<temp_dry_dry &le; 312.7223<br/>score = 0.4846>, fillcolor="#00000000"]; 0 -> 1 [labeldistance=2.5, labelangle=45, headlabel="True"]; 2 [label=<class = 2>, fillcolor="#00000000", shape=ellipse]; 0 -> 2 [labeldistance=2.5, labelangle=-45, headlabel="False"]; 3 [label=<temp_dry_dry &le; 311.7029<br/>score = 0.0071>, fillcolor="#00000000"]; 1 -> 3; 4 [label=<class = 1>, fillcolor="#00000000", shape=ellipse]; 1 -> 4; 5 [label=<class = 0>, fillcolor="#00000000", shape=ellipse]; 3 -> 5; 6 [label=<nir_dry_dry &le; 0.2232<br/>score = 0.5000>, fillcolor="#00000000"]; 3 -> 6; 7 [label=<class = 0>, fillcolor="#00000000", shape=ellipse]; 6 -> 7; 8 [label=<class = 1>, fillcolor="#00000000", shape=ellipse]; 6 -> 8; }
importance: Object (112 properties)
blue:0
blue_ampl:0
blue_dry_dry:0
blue_max:0
blue_min:0
blue_stdDev:0
blue_wet_wet:0
cai:0
cai_ampl:0
cai_dry_dry:0
cai_max:0
cai_min:0
cai_stdDev:0
cai_wet_wet:0
evi2:0
evi2_ampl:0
evi2_dry_dry:0
evi2_max:0
evi2_min:0
evi2_stdDev:0
evi2_wet_wet:0
gcvi:0
gcvi_ampl:0
gcvi_dry_dry:0
gcvi_max:0
gcvi_min:0
gcvi_stdDev:0
gcvi_wet_wet:0
green:0
green_ampl:0
green_dry_dry:0
green_max:0
green_min:0
green_stdDev:0
green_wet_wet:0
hall_cover:0
hall_cover_ampl:0
hall_cover_dry_dry:0
hall_cover_max:0
hall_cover_min:0
hall_cover_stdDev:0
hall_cover_wet_wet:0
mndwi:0.33146184237887305
mndwi_ampl:0
mndwi_dry_dry:0
mndwi_max:0
mndwi_min:0
mndwi_stdDev:0
mndwi_wet_wet:0
ndbi:0
ndbi_ampl:0
ndbi_dry_dry:0
ndbi_max:0
ndbi_min:0
ndbi_stdDev:0
ndbi_wet_wet:0
ndvi:0
ndvi_ampl:0
ndvi_dry_dry:0
ndvi_max:0
ndvi_min:0
ndvi_stdDev:0
ndvi_wet_wet:0
ndwi:0
ndwi_ampl:0
ndwi_dry_dry:0
ndwi_max:0
ndwi_min:0
ndwi_stdDev:0
ndwi_wet_wet:0
nir:0
nir_ampl:0
nir_dry_dry:0.5
nir_max:0
nir_min:0
nir_stdDev:0
nir_wet_wet:0
pri:0
pri_ampl:0
pri_dry_dry:0
pri_max:0
pri_min:0
pri_stdDev:0
pri_wet_wet:0
red:0
red_ampl:0
red_dry_dry:0
red_max:0
red_min:0
red_stdDev:0
red_wet_wet:0
swir1:0
swir1_ampl:0
swir1_dry_dry:0
swir1_max:0
swir1_min:0
swir1_stdDev:0
swir1_wet_wet:0
swir2:0
swir2_ampl:0
swir2_dry_dry:0
swir2_max:0
swir2_min:0
swir2_stdDev:0
swir2_wet_wet:0
temp:0
temp_ampl:0
temp_dry_dry:0.4917197959931788
temp_max:0
temp_min:0
temp_stdDev:0
temp_wet_wet:0
maxDepth:5
tree:n= 2400 node), split, n, loss, yval, (yprob) * denotes terminal node 1) root 2400 1600.0 0 (0.33333 0.33333 0.33333) 2) mndwi<=-0.382401 1603 804.49 0 (0.49875 0.49875 0.0024907) 4) temp_dry_dry<=312.722 810 23.711 0 (0.98278 0.012300 0.0049200) 8) temp_dry_dry<=311.703 798 11.932 0 (0.99001 0.0049938 0.0049938) * 9) temp_dry_dry>311.703 12 6.0000 0 (0.46667 0.46667 0.066667) 18) nir_dry_dry<=0.223239 6 0.0000 0 (0.77778 0.11111 0.11111) * 19) nir_dry_dry>0.223239 6 0.0000 1 (0.11111 0.77778 0.11111) * 5) temp_dry_dry>312.722 793 3.9899 1 (0.0037688 0.99497 0.0012563) * 3) mndwi>-0.382401 797 0.0000 2 (0.0012500 0.0012500 0.99750) *
+
-
Draw a polyline
Draw a polygon
Draw a rectangle
Draw a marker
Edit layers
Delete layers

All layers on/off

OpenStreetMap.Mapnik


Landsat — RGB


CART — floresta x agricultura


Polígonos — floresta


Polígonos — agricultura


Polígonos — água

Measure

30 km
10 mi
ipyleaflet | © OpenStreetMap contributors, Google Earth Engine
Matriz de confusão — treinamento:
[[798, 2, 0], [3, 797, 0], [3, 0, 797]]
Acurácia de treinamento: 0.9966666666666667

Matriz de confusão — validação:
[[796, 4], [40, 760]]
Acurácia de validação: 0.9725
Kappa de validação: 0.9450000000000001
Acurácia do produtor: [[0.995], [0.95]]
Acurácia do consumidor: [[0.9521531100478469, 0.9947643979057592]]