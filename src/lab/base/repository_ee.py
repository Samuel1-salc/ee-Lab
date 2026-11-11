"""Utilitários reutilizáveis para análises com Google Earth Engine e geemap.

O módulo separa cinco responsabilidades:
  * aquisição de coleções/feições;
  * pré-processamento Landsat 8 e geração de índices;
  * preparação de amostras, treinamento e avaliação de classificadores;
  * visualização no geemap com presets consistentes;
  * exportação de produtos (RGB, NDVI, feature space e classes).

As funções devolvem objetos server-side do Earth Engine. Só use ``getInfo()``
para inspecções pequenas, nunca para baixar uma imagem inteira.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import ee


# Assets e parâmetros de visualização compartilhados pelo projeto.
LANDSAT_8_L2 = "LANDSAT/LC08/C02/T1_L2"
PROJECT = "lateral-spirit-514212-j0"
MAPBIOMAS_AGRICULTURE_CYCLES = (
    "projects/mapbiomas-public/assets/brazil/lulc/collection11/"
    "mapbiomas_brazil_collection11_agriculture_number_cycles_v1"
)
MAPBIOMAS_PASTURE_AGE = (
    "projects/mapbiomas-public/assets/brazil/lulc/collection11/"
    "mapbiomas_brazil_collection11_pasture_age_v1"
)

ASSET_ID_AGRICULTURA = (
    "projects/poetic-tesla-506814-e1/assets/amostras/tocantins_2025_AGRICULTURA"
)

VIS_RGB: dict[str, Any] = {"bands": ["red", "green", "blue"], "min": 0.02, "max": 0.30}
VIS_FALSE_COLOR_NIR: dict[str, Any] = {
    "bands": ["nir", "red", "green"],
    "min": 0.02,
    "max": 0.45,
}
VIS_NDVI: dict[str, Any] = {
    "bands": ["ndvi"],
    "min": -0.20,
    "max": 0.85,
    "palette": ["8c510a", "f6e8c3", "c7eae5", "01665e"],
}

VIS_NDWI: dict[str, Any] = {
    "bands": ["ndwi"],
    "min": -0.5,
    "max": 0.5,
    "palette": ["brown", "white", "blue"],
}
VIS_MNDWI: dict[str, Any] = {
    "bands": ["mndwi"],
    "min": -0.5,
    "max": 0.5,
    "palette": ["8c510a", "f7f7f7", "0066ff"],
}
VIS_NDBI: dict[str, Any] = {
    "bands": ["ndbi"],
    "min": -0.5,
    "max": 0.5,
    "palette": ["006837", "f7f7f7", "a6611a"],
}

VIS_CLASSES: dict[str, Any] = {
    "bands": ["classe"],
    "min": 1,
    "max": 2,
    "palette": ["d73027", "1a9850"],  # 1=pastagem, 2=agricultura
}
VIS_LABELS: dict[str, Any] = {
    "bands": ["classe_local"],
    "min": 1,
    "max": 4,
    "palette": ["d73027", "1a9850", "fdae61", "ff0000"],  # 1=pastagem, 2=agricultura, 3=água, 4=urbano
}


def AuthenticateEarhEngine(force: bool = False) -> None:
    if force or not ee.data._credentials:
        ee.Authenticate()

def initialize_earth_engine(project: str | None = None, use_eerepr: bool = True) -> None:
    """Inicializa Earth Engine e, em notebooks, o renderizador opcional eerepr."""
    if project:
        ee.Initialize(project=project)
    else:
        ee.Initialize()

    if use_eerepr:
        try:
            import eerepr

            eerepr.initialize()
        except ImportError:
            # eerepr apenas melhora a visualização no notebook; não é requisito.
            pass


@dataclass(frozen=True)
class PeriodoAgricola:
    """Janelas temporais da análise para um ano agrícola no Tocantins."""

    ano: int
    inicio_anual: str
    fim_anual: str
    inicio_seca: str  
    fim_seca: str
    inicio_chuva: str
    fim_chuva: str

    @classmethod
    def tocantins(cls, ano: int) -> "PeriodoAgricola":
        """Cria as janelas anual, seca e chuvosa para o ano informado.

        Args:
            ano: Ano civil usado como referência para a análise.

        Returns:
            Período agrícola com datas no formato ISO ``AAAA-MM-DD``. A
            estação chuvosa começa em 16 de outubro do ano anterior.
        """
        return cls(
            ano=ano,
            inicio_anual=f"{ano}-01-01",
            # filterDate usa limite final exclusivo. 01/jan do ano seguinte inclui 31/dez.
            fim_anual=f"{ano + 1}-01-01",
            inicio_seca=f"{ano}-05-01",
            fim_seca=f"{ano}-10-16",
            inicio_chuva=f"{ano - 1}-10-16",
            fim_chuva=f"{ano}-05-01",
        )


class GeometryUtils:
    """Criação e métricas de regiões de interesse (AOI)."""

    @staticmethod
    def polygon(coordinates: Sequence[Sequence[float]]) -> ee.Geometry:
        """Cria um polígono. A última coordenada deve fechar o anel."""
        return ee.Geometry.Polygon([list(coordinates)])

    @staticmethod
    def metrics(geometry: ee.Geometry, max_error: float = 1) -> dict[str, float]:
        """Obtém métricas pequenas da AOI no cliente, para relatório/notebook."""
        area_m2 = geometry.area(maxError=max_error).getInfo()
        perimeter_m = geometry.perimeter(maxError=max_error).getInfo()
        return {
            "area_m2": area_m2,
            "area_hectares": area_m2 / 10_000,
            "area_km2": area_m2 / 1_000_000,
            "perimetro_m": perimeter_m,
            "perimetro_km": perimeter_m / 1_000,
        }

    @staticmethod
    def boundary_side_km(coordinates: Sequence[Sequence[float]], max_error: float = 1) -> float:
        """Calcula, em quilômetros, o primeiro lado do contorno informado.

        Args:
            coordinates: Coordenadas do contorno; os dois primeiros pontos
                definem o segmento medido.
            max_error: Erro máximo, em metros, aceito pelo Earth Engine.

        Returns:
            Comprimento do segmento em quilômetros, transferido ao cliente.
        """
        return ee.Geometry.LineString([coordinates[0], coordinates[1]]).length(
            maxError=max_error
        ).getInfo() / 1_000


class CollectionUtils:
    """Ponto único para carregar e filtrar ImageCollection/FeatureCollection."""

    @staticmethod
    def image(source: str | ee.Image) -> ee.Image:
        """Normaliza um asset ou uma imagem já instanciada como ee.Image."""
        return ee.Image(source) if isinstance(source, str) else source
    
    @staticmethod
    def image_collection(source: str | ee.ImageCollection) -> ee.ImageCollection:
        """Normaliza um asset ou uma coleção como ``ee.ImageCollection``.

        Args:
            source: ID de um asset ou coleção já instanciada.

        Returns:
            Coleção de imagens correspondente à fonte.
        """
        return ee.ImageCollection(source) if isinstance(source, str) else source

    @staticmethod
    def feature_collection(source: str | ee.FeatureCollection) -> ee.FeatureCollection:
        """Normaliza um asset ou uma coleção como ``ee.FeatureCollection``.

        Args:
            source: ID de um asset ou coleção de feições já instanciada.

        Returns:
            Coleção de feições correspondente à fonte.
        """
        return ee.FeatureCollection(source) if isinstance(source, str) else source

    @classmethod
    def extract_images(
        cls,
        source: str | ee.ImageCollection,
        geometry: ee.Geometry,
        start_date: str,
        end_date: str,
        bands: Sequence[str] | None = None,
    ) -> ee.ImageCollection:
        """Retorna a ImageCollection espacial e temporalmente filtrada."""
        collection = cls.image_collection(source).filterBounds(geometry).filterDate(start_date, end_date)
        return collection.select(list(bands)) if bands else collection

    @classmethod
    def extract_features(
        cls,
        source: str | ee.FeatureCollection,
        geometry: ee.Geometry | None = None,
        property_filters: Mapping[str, Any] | None = None,
    ) -> ee.FeatureCollection:
        """Retorna feições filtradas por AOI e igualdade de propriedades."""
        collection = cls.feature_collection(source)
        if geometry is not None:
            collection = collection.filterBounds(geometry)
        for field, value in (property_filters or {}).items():
            collection = collection.filter(ee.Filter.eq(field, value))
        return collection


class Landsat8:
    """Pré-processamento Landsat 8 C2 L2 e composições temporais."""

    @staticmethod
    def prepare_surface_reflectance(image: ee.Image) -> ee.Image:
        """Mascara pixels ruins/saturados e aplica escala/offset oficiais da cena."""
        qa_mask = image.select("QA_PIXEL").bitwiseAnd(int("11111", 2)).eq(0)
        saturation_mask = image.select("QA_RADSAT").eq(0)

        def factor_image(names: list[str]) -> ee.Image:
            """Converte metadados de escala ou offset em imagem constante."""
            return ee.Image.constant(image.toDictionary().select(names).values())

        scale = factor_image(["REFLECTANCE_MULT_BAND_.|TEMPERATURE_MULT_BAND_ST_B10"])
        offset = factor_image(["REFLECTANCE_ADD_BAND_.|TEMPERATURE_ADD_BAND_ST_B10"])
        scaled = image.select("SR_B.|ST_B10").multiply(scale).add(offset)
        return image.addBands(scaled, None, True).updateMask(qa_mask).updateMask(saturation_mask)

    @staticmethod
    def add_indices(image: ee.Image) -> ee.Image:
        """Padroniza bandas Landsat e acrescenta índices espectrais."""
        # Azul (0,45–0,51 µm): água rasa, aerossóis e composição em cor natural.
        blue = image.select("SR_B2").rename("blue")
        # Verde (0,53–0,59 µm): vigor da vegetação e contraste com corpos d'água.
        green = image.select("SR_B3").rename("green")
        # Vermelho (0,64–0,67 µm): absorção pela clorofila e discriminação da vegetação.
        red = image.select("SR_B4").rename("red")
        # Infravermelho próximo (0,85–0,88 µm): biomassa e estrutura da vegetação.
        nir = image.select("SR_B5").rename("nir")
        # SWIR 1 (1,57–1,65 µm): umidade da vegetação/solo e áreas construídas.
        swir1 = image.select("SR_B6").rename("swir1")
        # SWIR 2 (2,11–2,29 µm): secura, minerais, queimadas e solo exposto.
        swir2 = image.select("SR_B7").rename("swir2")
        # Temperatura de superfície derivada da banda termal 10 do Landsat.
        temp = image.select("ST_B10").rename("temp")

        # NDVI: diferença normalizada entre NIR e vermelho; indica vegetação verde.
        ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")
        # EVI2: índice de vegetação que reduz saturação e influência do solo sem usar azul.
        evi2 = image.expression(
            "2.5 * ((NIR - RED) / (NIR + 2.4 * RED + 1.0))", {"NIR": nir, "RED": red}
        ).rename("evi2")
        # CAI: razão SWIR2/SWIR1 usada aqui para realçar diferenças em resíduos e secura.
        cai = swir2.divide(swir1).rename("cai")
        # NDWI (NIR/SWIR1, também chamado NDMI): sensível à umidade da vegetação e do solo.
        ndwi = nir.subtract(swir1).divide(nir.add(swir1)).rename("ndwi")
        # MNDWI: diferença normalizada Green/SWIR1; destaca água e reduz resposta urbana.
        mndwi = green.subtract(swir1).divide(green.add(swir1)).rename("mndwi")
        # NDBI: diferença normalizada SWIR1/NIR; realça construções e também solo exposto.
        ndbi = swir1.subtract(nir).divide(swir1.add(nir)).rename("ndbi")
        # GCVI: razão NIR/verde menos 1; relacionado à clorofila e ao vigor vegetal.
        gcvi = nir.divide(green).subtract(1).rename("gcvi")
        # Hall Cover: transformação espectral empírica para estimar cobertura vegetal.
        hall_cover = image.expression(
            "(-1.0 * RED * 0.017) - (NIR * 0.007) - (SWIR2 * 0.079) + 5.22",
            {"RED": red, "NIR": nir, "SWIR2": swir2},
        ).rename("hall_cover")
        # PRI: razão normalizada azul/verde usada como aproximação da resposta fotossintética.
        pri = blue.subtract(green).divide(blue.add(green)).rename("pri")

        return image.addBands(
            [
                blue,
                green,
                red,
                nir,
                swir1,
                swir2,
                temp,
                ndvi,
                evi2,
                cai,
                ndwi,
                mndwi,
                ndbi,
                gcvi,
                hall_cover,
                pri,
            ]
        ).select(
            [
                "blue",
                "green",
                "red",
                "nir",
                "swir1",
                "swir2",
                "temp",
                "ndvi",
                "evi2",
                "cai",
                "ndwi",
                "mndwi",
                "ndbi",
                "gcvi",
                "hall_cover",
                "pri",
            ]
        )

    @classmethod
    def collection(cls, geometry: ee.Geometry, period: PeriodoAgricola) -> ee.ImageCollection:
        """Coleção-base incluindo a janela chuvosa que começa no ano anterior."""                                                                                                                                                                                   
        # Já retorna a coleção com bandas Landsat e índices espectrais, prontos para o feature space.                                                                                                                                               
        raw = CollectionUtils.extract_images(
            LANDSAT_8_L2, geometry, period.inicio_chuva, period.fim_anual
        )
        return raw.map(cls.prepare_surface_reflectance).map(cls.add_indices)

    @staticmethod
    def feature_space(
        collection: ee.ImageCollection, geometry: ee.Geometry, period: PeriodoAgricola
    ) -> ee.Image:
        """Gera variáveis anuais, secas, chuvosas, variabilidade e amplitude."""
        # A coleção contém outubro--dezembro do ano anterior. As métricas anuais
        # abaixo devem considerar somente o ano solicitado.
        annual = collection.filterDate(period.inicio_anual, period.fim_anual)
        median_all = annual.median()
        median_dry = annual.filterDate(period.inicio_seca, period.fim_seca).median().regexpRename(
            "(.*)", "$1_dry"
        )
        # A estação chuvosa cruza o ano civil: outubro--dez + janeiro--abril.
        median_wet = collection.filterDate(period.inicio_chuva, period.fim_chuva).median().regexpRename("(.*)", "$1_wet")
        std = annual.reduce(ee.Reducer.stdDev()).regexpRename("(.*)_stdDev", "$1_stdDev")
        minimum = annual.reduce(ee.Reducer.min()).regexpRename("(.*)_min", "$1_min")
        maximum = annual.reduce(ee.Reducer.max()).regexpRename("(.*)_max", "$1_max")
        amplitude = maximum.subtract(minimum).regexpRename("(.*)_max", "$1_ampl")
        return ee.Image.cat([median_all, median_dry, median_wet, std, minimum, maximum, amplitude]).clip(geometry)

    @staticmethod
    def green_peak(
        collection: ee.ImageCollection, geometry: ee.Geometry, period: PeriodoAgricola | None = None
    ) -> ee.Image:
        """Cena-mosaico com maior NDVI por pixel, limitada ao ano se informado."""
        selected = (
            collection.filterDate(period.inicio_anual, period.fim_anual) if period else collection
        )
        return selected.qualityMosaic("ndvi").clip(geometry)


class MapBiomasLabels:
    """Produz a banda ``classe``: 1=pastagem e 2=agricultura (prioritária)."""

    @staticmethod
    def binary_mask(asset: str, year: int, geometry: ee.Geometry) -> ee.Image:
        """Converte a classificação anual de um asset em máscara binária.

        Args:
            asset: ID do asset MapBiomas com bandas anuais.
            year: Ano da banda ``classification_<ano>``.
            geometry: Região usada para recortar o resultado.

        Returns:
            Imagem binária não mascarada, em que valores maiores que zero são
            convertidos para um.
        """
        return ee.Image(asset).select(f"classification_{year}").gt(0).unmask(0, False).clip(geometry)

    @classmethod
    def pasture_and_agriculture(cls, year: int, geometry: ee.Geometry) -> ee.Image:
        """Combina máscaras MapBiomas em classes de pastagem e agricultura.

        Args:
            year: Ano das classificações utilizadas.
            geometry: Região usada para recortar as máscaras.

        Returns:
            Imagem byte denominada ``classe``, com 1 para pastagem e 2 para
            agricultura. Agricultura tem prioridade em pixels sobrepostos e
            pixels sem classe permanecem mascarados.
        """
        agriculture = cls.binary_mask(MAPBIOMAS_AGRICULTURE_CYCLES, year, geometry)
        pasture = cls.binary_mask(MAPBIOMAS_PASTURE_AGE, year, geometry)
        return (
            pasture.multiply(0)
            .where(pasture.And(agriculture.Not()), 1)
            .where(agriculture, 2)
            .rename("classe")
            .selfMask()
            .toByte()
        )


class LocalLabels:
    """Converte pontos ou polígonos locais em uma banda de rótulos raster.

    A FeatureCollection deve ter uma propriedade numérica por feição, por
    padrão ``classe``. Por exemplo: 1=pastagem, 2=agricultura, 3=solo exposto.
    Por padrão, pixels fora das feições permanecem mascarados: não são tratados
    acidentalmente como a classe zero durante o treinamento.
    """

    @staticmethod
    def from_feature_collection(
        features: str | ee.FeatureCollection,
        class_property: str = "classe",
        geometry: ee.Geometry | None = None,
        reference_image: ee.Image | None = None,
        band_name: str = "classe",
        default_class: int | None = None,
        background_value: int | None = None,
    ) -> ee.Image:
        """Rasteriza uma FeatureCollection local usando sua classe como pixel.

        Args:
            features: ``ee.FeatureCollection`` desenhada no Jupyter/geemap ou
                o id de um asset FeatureCollection no Earth Engine.
            class_property: nome da propriedade inteira com o rótulo de cada
                feição. Exemplos: ``classe`` ou ``class_id``.
            geometry: AOI final. Também descarta feições fora dela.
            reference_image: imagem de referência para herdar a projeção/grid,
                normalmente o ``feature_space`` Landsat.
            band_name: nome da banda produzida.
            default_class: define uma única classe para todas as feições; útil
                quando cada Feature não possui a propriedade de classe.
            background_value: se ``None``, o exterior fica mascarado. Use 0
                somente quando zero for de fato uma classe válida.

        Returns:
            ee.Image inteira de 16 bits, com uma banda de rótulo.
        """
        collection = CollectionUtils.feature_collection(features)
        if geometry is not None:
            collection = collection.filterBounds(geometry)
        if default_class is not None:
            collection = collection.map(
                lambda feature: feature.set(class_property, default_class)
            )

        labels = collection.reduceToImage(
            properties=[class_property], reducer=ee.Reducer.first()
        ).rename(band_name).toInt16()

        # Mantém a grade espacial consistente com o feature space / Landsat.
        # setDefaultProjection não força um recálculo antecipado como reproject.
        if reference_image is not None:
            labels = labels.setDefaultProjection(reference_image.select(0).projection())
        if geometry is not None:
            labels = labels.clip(geometry)
        if background_value is not None:
            labels = labels.unmask(background_value).toInt16()
        return labels

    @staticmethod
    def attach_to_features(feature_space: ee.Image, labels: ee.Image) -> ee.Image:
        """Acrescenta a banda de rótulo ao feature space sem alterar as bandas existentes."""
        return feature_space.addBands(labels)




class MapLayers:
    """Camadas prontas para o geemap. Cada método recebe uma ee.Image já criada."""

    @staticmethod
    def create(geometry: ee.Geometry, zoom: int = 8):
        """Cria um mapa geemap centralizado na região de interesse.

        Args:
            geometry: Geometria usada como centro e referência de extensão.
            zoom: Nível inicial de aproximação do mapa.

        Returns:
            Instância de ``geemap.Map`` pronta para receber camadas.
        """
        import geemap

        mapa = geemap.Map()
        mapa.centerObject(geometry, zoom)
        return mapa

    @staticmethod
    def add_image(map_objetct : Any, image: ee.Image, name: str = "Área uploaded0") -> None:
        """Adiciona no mapa uma image Layer ao mapa"""
        map_objetct.addLayer(image,{},name)


    @staticmethod
    def add_aoi(map_object: Any, geometry: ee.Geometry, name: str = "Área de estudo") -> None:
        """Adiciona ao mapa o contorno da área de interesse.

        Args:
            map_object: Mapa geemap que receberá a camada.
            geometry: Geometria da área de interesse.
            name: Nome exibido no controle de camadas.
        """
        map_object.addLayer(geometry, {}, name)

    @staticmethod
    def add_rgb(map_object: Any, image: ee.Image, name: str = "Landsat — RGB") -> ee.Image:
        """Adiciona uma composição Landsat em cores naturais ao mapa.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem com as bandas ``red``, ``green`` e ``blue``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select(["red", "green", "blue"])
        map_object.addLayer(sub_image, VIS_RGB, name)
    

    @staticmethod
    def add_false_color(map_object: Any, image: ee.Image, name: str = "Landsat — falsa cor NIR") -> ee.Image:
        """Adiciona ao mapa uma composição de falsa cor com infravermelho.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem com as bandas ``nir``, ``red`` e ``green``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select(["nir", "red", "green"])
        map_object.addLayer(sub_image, VIS_FALSE_COLOR_NIR, name)

    
    @staticmethod
    def add_ndvi(map_object: Any, image: ee.Image, name: str = "NDVI") -> ee.Image:
        """Adiciona a banda ``ndvi`` ao mapa com o preset do módulo.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem que contém a banda ``ndvi``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select["ndvi"]
        map_object.addLayer(sub_image, VIS_NDVI, name)

    @staticmethod
    def add_ndwi(map_object: Any, image: ee.Image, name: str = "NDWI") -> None:
        """Adiciona a banda ``ndwi`` ao mapa com o preset do módulo.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem que contém a banda ``ndwi``.
            name: Nome exibido no controle de camadas.
        """
        map_object.addLayer(image.select("ndwi"), VIS_NDWI, name)

    @staticmethod
    def add_mndwi(map_object: Any, image: ee.Image, name: str = "MNDWI") -> None:
        """Adiciona a banda ``mndwi`` ao mapa com o preset do módulo.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem que contém a banda ``mndwi``.
            name: Nome exibido no controle de camadas.
        """
        map_object.addLayer(image.select("mndwi"), VIS_MNDWI, name)

    @staticmethod
    def add_ndbi(map_object: Any, image: ee.Image, name: str = "NDBI") -> ee.Image:
        """Adiciona a banda ``ndbi`` ao mapa com o preset do módulo.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem que contém a banda ``ndbi``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select["ndwi"]
        map_object.addLayer(sub_image, VIS_NDBI, name)

    @staticmethod
    def add_classes(map_object: Any, image: ee.Image, name: str = "Classes MapBiomas") -> None:
        """Adiciona a banda padronizada ``classe`` ao mapa."""
        map_object.addLayer(image.select("classe"), VIS_CLASSES, name)

    @staticmethod
    def add_labels(
        map_object: Any,
        image: ee.Image,
        band_name: str = "classe_local",
        name: str = "Amostras de treinamento",
        vis_params: Mapping[str, Any] | None = None,
    ) -> None:
        """Adiciona uma banda de labels, permitindo informar seu nome real."""
        params = dict(vis_params) if vis_params is not None else dict(VIS_LABELS)
        params["bands"] = [band_name]
        map_object.addLayer(
            image.select(band_name),
            params,
            name,
        )




class LayersToExport:

    @staticmethod
    def var_ndvi_to_Export(map_object: Any, image: ee.Image, name: str = "NDVI") -> ee.Image:
        """Adiciona a banda ``ndvi`` ao mapa com o preset do módulo.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem que contém a banda ``ndvi``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select["ndvi"]
        map_object.addLayer(sub_image, VIS_NDVI, name)
        return sub_image

    @staticmethod
    def var_nir_to_Export(map_object: Any, image: ee.Image, name: str = "Landsat — falsa cor NIR") -> ee.Image:
        """Adiciona ao mapa uma composição de falsa cor com infravermelho.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem com as bandas ``nir``, ``red`` e ``green``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select(["nir", "red", "green"])
        map_object.addLayer(sub_image, VIS_FALSE_COLOR_NIR, name)
        return sub_image
    
    @staticmethod
    def var_ndbi_To_Export(map_object: Any, image: ee.Image, name: str = "NDBI") -> ee.Image:
        """Adiciona a banda ``ndbi`` ao mapa com o preset do módulo.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem que contém a banda ``ndbi``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select["ndwi"]
        map_object.addLayer(sub_image, VIS_NDBI, name)
        return sub_image

    @staticmethod
    def var_rgb_To_Export(map_object: Any, image: ee.Image, name: str = "Landsat — RGB") -> ee.Image:
        """Adiciona uma composição Landsat em cores naturais ao mapa.

        Args:
            map_object: Mapa geemap que receberá a camada.
            image: Imagem com as bandas ``red``, ``green`` e ``blue``.
            name: Nome exibido no controle de camadas.
        """
        sub_image = image.select(["red", "green", "blue"])
        map_object.addLayer(sub_image, VIS_RGB, name)
        return sub_image




class Exports:
    """Cria tarefas de exportação para o Google Drive; execute ``task.start()``."""
    LIMITAR_IMAGEM : dict[str, Any] =  {
        "multiespectrais" : 2048,
        "OneBand" : 4048,
    }

    @staticmethod
    def image_to_drive(
        image: ee.Image,
        description: str,
        region: ee.Geometry,
        folder: str = "earth_engine",
        scale: int = 30,
        crs: str = "EPSG:4326",
        file_format: str = "GeoTIFF",
        maxPixels: int = 1e13,
        fileDimensions: int = LIMITAR_IMAGEM["multiespectrais"], #limita o tamanho do bloco
        
    ) -> ee.batch.Task:
        """Cria uma tarefa de exportação de imagem para o Google Drive.

        Args:
            image: Imagem que será recortada e exportada.
            description: Identificador da tarefa no Earth Engine.
            region: Região de recorte e exportação.
            folder: Pasta de destino no Google Drive.
            scale: Resolução espacial, em metros por pixel.
            crs: Sistema de referência de coordenadas da saída.
            file_format: Formato de arquivo aceito pelo Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada; chame ``start()``.
        """
        return ee.batch.Export.image.toDrive(
            image=image.clip(region),
            description=description,
            folder=folder,
            region=region,
            scale=scale,
            crs=crs,
            maxPixels=maxPixels,
            fileFormat=file_format,
            fileDimensions=fileDimensions,
        )

    @classmethod
    def rgb_to_drive(cls, image: ee.Image, region: ee.Geometry, description: str = "landsat_rgb") -> ee.batch.Task:
        """Cria uma tarefa para exportar as bandas RGB ao Google Drive.

        Args:
            image: Imagem com bandas ``red``, ``green`` e ``blue``.
            region: Região de recorte e exportação.
            description: Identificador da tarefa no Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada.
        """
        return cls.image_to_drive(image.select(["red", "green", "blue"]), description, region)

    @classmethod
    def ndvi_to_drive(cls, image: ee.Image, region: ee.Geometry, description: str = "landsat_ndvi") -> ee.batch.Task:
        """Cria uma tarefa para exportar a banda NDVI ao Google Drive.

        Args:
            image: Imagem que contém a banda ``ndvi``.
            region: Região de recorte e exportação.
            description: Identificador da tarefa no Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada.
        """
        return cls.image_to_drive(image.select("ndvi"), description, region)

    @classmethod
    def ndwi_to_drive(cls, image: ee.Image, region: ee.Geometry, description: str = "landsat_ndwi") -> ee.batch.Task:
        """Cria uma tarefa para exportar a banda NDWI ao Google Drive.

        Args:
            image: Imagem que contém a banda ``ndwi``.
            region: Região de recorte e exportação.
            description: Identificador da tarefa no Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada.
        """
        return cls.image_to_drive(image.select("ndwi"), description, region)

    @classmethod
    def mndwi_to_drive(cls, image: ee.Image, region: ee.Geometry,
    description: str = "landsat_mndwi") -> ee.batch.Task:
            """Cria uma tarefa para exportar a banda MNDWI ao Google Drive.
    
            Args:
                image: Imagem que contém a banda ``mndwi``.
                region: Região de recorte e exportação.
                description: Identificador da tarefa no Earth Engine.
    
            Returns:
                Tarefa de exportação ainda não iniciada.
            """
            return cls.image_to_drive(image.select("mndwi"), description, region)

    @classmethod
    def false_color_to_drive(cls,image: ee.Image, region: ee.Geometry, description: str = "landsat_false_color") -> ee.batch.Task:
        """cria uma tarefa para exportar a banda nir (false color) ao google drive

        Args:
            image : Imagem que contém a banda `nir`.
            region: Região de recorte e exportação 
            description : Identificador da tarefa no earth Engine

        Returns:
            Tarefa de eportação ainda não

        """
        return cls.image_to_drive(image.select("nir"),description,region)

    @classmethod
    def feature_space_to_drive(
        cls, image: ee.Image, region: ee.Geometry, description: str = "landsat_feature_space"
    ) -> ee.batch.Task:
        """Cria uma tarefa para exportar todo o espaço de atributos.

        Args:
            image: Imagem multibanda com os preditores.
            region: Região de recorte e exportação.
            description: Identificador da tarefa no Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada.
        """
        return cls.image_to_drive(image, description, region)

    @classmethod
    def feature_Collection_to_Assets_ee(
        cls, collection: ee.FeatureCollection, asset_id: str, description: str = "features"
    ) -> ee.batch.Task:
        """Cria uma tarefa para exportar feições como asset do Earth Engine.

        Args:
            collection: Coleção de feições que será persistida.
            asset_id: ID completo do asset de destino.
            description: Identificador da tarefa no Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada; chame ``start()``.
        """
        return ee.batch.Export.table.toAsset(
            collection=collection,
            description=description,
            assetId=asset_id,
        )
    
    @classmethod
    def image_to_assets(
         image: ee.Image, asset_id: str, description: str = "image_asset"
    ) -> ee.batch.Task:
        """Cria uma tarefa para exportar uma imagem como asset do Earth Engine.

        Args:
            image: Imagem que será persistida.
            asset_id: ID completo do asset de destino.
            description: Identificador da tarefa no Earth Engine.

        Returns:
            Tarefa de exportação ainda não iniciada; chame ``start()``.
        """
        return ee.batch.Export.image.toAsset(
            image=image,
            description=description,
            assetId=asset_id,
        )


class TimeSeries:
    """Extrai e desenha séries temporais por feição sem confundir Image e FeatureCollection."""

    @staticmethod
    def reduce_by_features(
        collection: ee.ImageCollection,
        features: ee.FeatureCollection,
        band: str = "ndvi",
        scale: int = 30,
    ) -> ee.FeatureCollection:
        """Calcula a média temporal de uma banda para cada feição.

        Args:
            collection: Coleção de imagens da série temporal.
            features: Regiões ou pontos usados na redução espacial.
            band: Banda selecionada em cada imagem.
            scale: Resolução espacial da redução, em metros.

        Returns:
            Coleção achatada com uma feição por imagem e região, contendo a
            média e a propriedade ``system:time_start``.
        """
        selected = collection.select(band)

        def per_image(image: ee.Image) -> ee.FeatureCollection:
            """Reduz uma imagem nas feições e preserva sua data de aquisição."""
            values = image.reduceRegions(collection=features, reducer=ee.Reducer.mean(), scale=scale)
            return values.map(lambda feature: feature.set("system:time_start", image.get("system:time_start")))

        return ee.FeatureCollection(selected.map(per_image).flatten())

    
    def plot_ndvi(
        cls,
        collection: ee.ImageCollection,
        features: ee.FeatureCollection,
        label_field: str = "label",
    ) -> None:
        """Desenha no cliente a série de NDVI médio agrupada por rótulo.

        Args:
            collection: Coleção de imagens que contém a banda ``ndvi``.
            features: Feições usadas para calcular as médias espaciais.
            label_field: Propriedade que identifica as séries no gráfico.

        Note:
            A função transfere os resultados reduzidos para um DataFrame local
            e exibe o gráfico imediatamente com Matplotlib.
        """
        import geemap
        import matplotlib.pyplot as plt
        import pandas as pd

        extracted = cls.reduce_by_features(collection, features)

        frame = geemap.ee_to_df(extracted, remove_geom=True)
        frame["date"] = pd.to_datetime(frame["system:time_start"], unit="ms")

        plt.figure(figsize=(10, 5))
        for label, group in frame.groupby(label_field):
            group = group.sort_values("date")
            plt.plot(group["date"], group["mean"], label=label, marker="o")

        plt.title("Série temporal do NDVI")
        plt.xlabel("Data")
        plt.ylabel("NDVI médio")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()
        plt.show()



class Models:
    """Treinamento e aplicação reutilizável de classificadores do Earth Engine.

    O fluxo esperado é: extrair os preditores nas regiões rotuladas, remapear
    as classes para inteiros consecutivos a partir de zero, separar treino e
    validação, treinar um algoritmo e avaliar as previsões independentes.
    """

    ALGORITHMS = ("random_forest", "cart", "naive_bayes")

    @staticmethod
    def random_forest(
        number_of_trees: int = 200,
        variables_per_split: int | None = None,
        min_leaf_population: int = 1,
        bag_fraction: float = 0.5,
        max_nodes: int | None = None,
        seed: int = 0,
    ) -> ee.Classifier:
        """Cria um Random Forest ainda não treinado."""
        return ee.Classifier.smileRandomForest(
            numberOfTrees=number_of_trees,
            variablesPerSplit=variables_per_split,
            minLeafPopulation=min_leaf_population,
            bagFraction=bag_fraction,
            maxNodes=max_nodes,
            seed=seed,
        )

    @staticmethod
    def cart(
        max_nodes: int | None = None,
        min_leaf_population: int = 1,
    ) -> ee.Classifier:
        """Cria uma árvore CART ainda não treinada."""
        return ee.Classifier.smileCart(
            maxNodes=max_nodes,
            minLeafPopulation=min_leaf_population,
        )

    @staticmethod
    def naive_bayes(smoothing: float = 1e-6) -> ee.Classifier:
        """Cria um Naive Bayes com o fator de suavização informado."""
        return ee.Classifier.smileNaiveBayes(lambda_=smoothing)

    @classmethod
    def create(cls, algorithm: str, **parameters: Any) -> ee.Classifier:
        """Cria um classificador pelo nome, aceitando aliases usuais."""
        normalized = algorithm.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "rf": "random_forest",
            "randomforest": "random_forest",
            "random_forest": "random_forest",
            "cart": "cart",
            "nb": "naive_bayes",
            "naivebayes": "naive_bayes",
            "naive_bayes": "naive_bayes",
        }
        selected = aliases.get(normalized)
        if selected is None:
            supported = ", ".join(cls.ALGORITHMS)
            raise ValueError(f"Algoritmo '{algorithm}' inválido. Use: {supported}.")

        factories = {
            "random_forest": cls.random_forest,
            "cart": cls.cart,
            "naive_bayes": cls.naive_bayes,
        }
        return factories[selected](**parameters)

    @staticmethod
    def sample_regions(
        feature_space: ee.Image,
        regions: str | ee.FeatureCollection,
        class_property: str = "class_id",
        bands: Sequence[str] | None = None,
        scale: int = 30,
        projection: ee.Projection | None = None,
        tile_scale: float = 2,
        geometries: bool = True,
    ) -> ee.FeatureCollection:
        """Extrai os valores dos preditores nos pontos ou polígonos rotulados."""
        predictors = feature_space.select(list(bands)) if bands is not None else feature_space
        return predictors.sampleRegions(
            collection=CollectionUtils.feature_collection(regions),
            properties=[class_property],
            scale=scale,
            projection=projection,
            tileScale=tile_scale,
            geometries=geometries,
        )

    @staticmethod
    def stratified_sample(
        feature_space: ee.Image,
        labels: ee.Image,
        class_band: str,
        region: ee.Geometry,
        num_points: int = 500,
        bands: Sequence[str] | None = None,
        class_values: Sequence[int] | None = None,
        class_points: Sequence[int] | None = None,
        scale: int = 30,
        projection: ee.Projection | None = None,
        seed: int = 0,
        tile_scale: float = 2,
        geometries: bool = False,
    ) -> ee.FeatureCollection:
        """Extrai uma quantidade controlada de pixels por classe.

        Evita materializar todos os pixels de polígonos extensos, o que pode
        causar ``Computed value is too large``. A imagem de rótulos deve ficar
        mascarada fora das regiões de treinamento.
        """
        predictors = feature_space.select(list(bands)) if bands is not None else feature_space
        image = predictors.addBands(labels.select(class_band), None, True)
        return image.stratifiedSample(
            numPoints=num_points,
            classBand=class_band,
            region=region,
            scale=scale,
            projection=projection,
            seed=seed,
            classValues=list(class_values) if class_values is not None else None,
            classPoints=list(class_points) if class_points is not None else None,
            dropNulls=True,
            tileScale=tile_scale,
            geometries=geometries,
        )

    @staticmethod
    def remap_classes(
        samples: ee.FeatureCollection,
        source_classes: Sequence[int],
        class_property: str = "class_id",
        target_classes: Sequence[int] | None = None,
    ) -> ee.FeatureCollection:
        """Remapeia rótulos para classes consecutivas, por padrão 0..N-1."""
        source = list(source_classes)
        target = list(target_classes) if target_classes is not None else list(range(len(source)))
        if len(source) != len(target):
            raise ValueError("source_classes e target_classes devem ter o mesmo tamanho.")
        if len(set(source)) != len(source):
            raise ValueError("source_classes não pode conter valores repetidos.")
        return ee.FeatureCollection(samples).remap(source, target, class_property)

    @staticmethod
    def split_samples(
        samples: ee.FeatureCollection,
        training_fraction: float = 0.7,
        seed: int = 0,
        random_column: str = "random",
    ) -> tuple[ee.FeatureCollection, ee.FeatureCollection]:
        """Divide aproximadamente as amostras em treino e validação."""
        if not 0 < training_fraction < 1:
            raise ValueError("training_fraction deve estar entre 0 e 1.")
        randomized = ee.FeatureCollection(samples).randomColumn(random_column, seed)
        training = randomized.filter(ee.Filter.lt(random_column, training_fraction))
        validation = randomized.filter(ee.Filter.gte(random_column, training_fraction))
        return training, validation

    @staticmethod
    def prepare_naive_bayes(
        feature_space: ee.Image,
        samples: ee.FeatureCollection,
        bands: Sequence[str] | ee.List,
        scale_factor: float = 1000,
        offset: float = 1_000_000,
    ) -> tuple[ee.Image, ee.FeatureCollection]:
        """Converte imagem e amostras para os mesmos preditores inteiros positivos.

        ``smileNaiveBayes`` descarta entradas negativas. A transformação deve
        ser idêntica no treinamento e na classificação; valores menores que
        um após escala e deslocamento são limitados a um.
        """
        band_list = ee.List(bands)
        prepared_image = (
            feature_space.select(band_list)
            .multiply(scale_factor)
            .round()
            .add(offset)
            .max(1)
            .toInt()
        )

        def prepare_feature(feature: ee.Feature) -> ee.Feature:
            """Aplica aos atributos da amostra a transformação da imagem."""
            values = band_list.map(
                lambda band: ee.Number(feature.get(ee.String(band)))
                .multiply(scale_factor)
                .round()
                .add(offset)
                .max(1)
                .toInt()
            )
            return feature.setMulti(ee.Dictionary.fromLists(band_list, values))

        prepared_samples = ee.FeatureCollection(samples).map(prepare_feature)
        return prepared_image, prepared_samples

    @classmethod
    def train(
        cls,
        samples: ee.FeatureCollection,
        input_properties: Sequence[str] | ee.List,
        class_property: str = "class_id",
        algorithm: str = "random_forest",
        classifier_parameters: Mapping[str, Any] | None = None,
        subsampling: float | None = None,
        subsampling_seed: int = 0,
    ) -> ee.Classifier:
        """Cria e treina um dos classificadores suportados."""
        classifier = cls.create(algorithm, **dict(classifier_parameters or {}))
        return classifier.train(
            features=ee.FeatureCollection(samples),
            classProperty=class_property,
            inputProperties=input_properties,
            subsampling=subsampling,
            subsamplingSeed=subsampling_seed,
        )

    @staticmethod
    def classify_image(
        feature_space: ee.Image,
        classifier: ee.Classifier,
        input_properties: Sequence[str] | ee.List | None = None,
        output_band: str = "classification",
    ) -> ee.Image:
        """Aplica um classificador treinado usando a mesma ordem de preditores."""
        predictors = (
            feature_space.select(input_properties)
            if input_properties is not None
            else feature_space
        )
        return predictors.classify(classifier, output_band)

    @staticmethod
    def training_metrics(classifier: ee.Classifier) -> dict[str, Any]:
        """Retorna matriz e métricas server-side do conjunto de treinamento."""
        matrix = classifier.confusionMatrix()
        return {
            "confusion_matrix": matrix,
            "accuracy": matrix.accuracy(),
            "kappa": matrix.kappa(),
            "producers_accuracy": matrix.producersAccuracy(),
            "consumers_accuracy": matrix.consumersAccuracy(),
        }

    @staticmethod
    def validation_metrics(
        classifier: ee.Classifier,
        validation_samples: ee.FeatureCollection,
        class_property: str = "class_id",
        prediction_property: str = "classification",
        class_order: Sequence[int] | ee.List | None = None,
    ) -> dict[str, Any]:
        """Classifica amostras independentes e retorna métricas server-side."""
        predictions = ee.FeatureCollection(validation_samples).classify(
            classifier, prediction_property
        )
        matrix = predictions.errorMatrix(
            class_property,
            prediction_property,
            class_order,
        )
        return {
            # Amostras de validação com a classe prevista em prediction_property.
            "predictions": predictions,
            # Matriz classes reais (linhas) x classes previstas (colunas).
            "confusion_matrix": matrix,
            # Proporção total de previsões corretas entre todas as amostras.
            "accuracy": matrix.accuracy(),
            # Concordância entre previsão e referência corrigida pelo acaso.
            "kappa": matrix.kappa(),
            # Acurácia do produtor (recall): acertos / total real de cada classe.
            "producers_accuracy": matrix.producersAccuracy(),
            # Acurácia do consumidor (precision): acertos / total previsto por classe.
            "consumers_accuracy": matrix.consumersAccuracy(),
        }

    @staticmethod
    def class_distribution(
        samples: ee.FeatureCollection,
        class_property: str = "class_id",
    ) -> ee.Dictionary:
        """Conta as amostras por classe sem transferir o resultado ao cliente."""
        return ee.FeatureCollection(samples).aggregate_histogram(class_property)
