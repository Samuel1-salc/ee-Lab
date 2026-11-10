import ee
import geemap
import ipywidgets as widgets
from uuid import uuid4

ee.Initialize()

# Mapa
m = geemap.Map(center=(-10.18, -48.33), zoom=11)
m.add_draw_control()

draw = m.draw_control


# ---------- Widgets ----------
seletor = widgets.Dropdown(
    options=[],
    description="Polígono:",
    layout=widgets.Layout(width="300px")
)

nome_classe = widgets.Text(
    placeholder="Ex.: Vegetação, Água, Solo exposto",
    description="Classe:",
    layout=widgets.Layout(width="300px")
)

codigo_classe = widgets.IntText(
    value=0,
    description="ID:",
    layout=widgets.Layout(width="180px")
)

btn_salvar = widgets.Button(
    description="Salvar classe",
    button_style="success",
    icon="save"
)

btn_excluir = widgets.Button(
    description="Excluir polígono",
    button_style="danger",
    icon="trash"
)

status = widgets.HTML("<i>Desenhe um polígono para começar.</i>")

painel = widgets.VBox([
    widgets.HTML("<b>Amostras de treinamento</b>"),
    seletor,
    nome_classe,
    codigo_classe,
    widgets.HBox([btn_salvar, btn_excluir]),
    status,
])


# ---------- Funções auxiliares ----------
def obter_geometria_selecionada():
    """Retorna a geometria cuja UUID está selecionada."""
    poligono_id = seletor.value

    if poligono_id is None:
        return None

    for geometria in draw.geometries:
        props = draw.get_geometry_properties(geometria) or {}

        if props.get("id") == poligono_id:
            return geometria

    return None


def atualizar_lista(selecionar_id=None):
    """Reconstrói a lista a partir do estado atual do DrawControl."""
    opcoes = []

    for indice, geometria in enumerate(draw.geometries, start=1):
        props = draw.get_geometry_properties(geometria) or {}

        poligono_id = props.get("id")
        classe = props.get("classe", "Sem classe")

        if poligono_id:
            opcoes.append(
                (f"{indice}. {classe}", poligono_id)
            )

    seletor.options = opcoes

    if selecionar_id and any(valor == selecionar_id for _, valor in opcoes):
        seletor.value = selecionar_id
    elif opcoes:
        seletor.value = opcoes[-1][1]


def ao_criar_poligono(_, geometria):
    """Executado automaticamente ao terminar um novo desenho."""
    poligono_id = str(uuid4())

    draw.set_geometry_properties(
        geometria,
        {
            "id": poligono_id,
            "classe": "Sem classe",
            "class_id": 0
        }
    )

    atualizar_lista(selecionar_id=poligono_id)
    status.value = "<span style='color:green'>Polígono criado. Agora defina a classe.</span>"


def ao_selecionar(change):
    geometria = obter_geometria_selecionada()

    if geometria is None:
        return

    props = draw.get_geometry_properties(geometria) or {}

    nome_classe.value = props.get("classe", "")
    codigo_classe.value = props.get("class_id", 0)


def salvar_classe(_):
    geometria = obter_geometria_selecionada()
    classe = nome_classe.value.strip()

    if geometria is None:
        status.value = "<span style='color:red'>Selecione um polígono.</span>"
        return

    if not classe:
        status.value = "<span style='color:red'>Informe o nome da classe.</span>"
        return

    props_antigas = draw.get_geometry_properties(geometria) or {}

    draw.set_geometry_properties(
        geometria,
        {
            **props_antigas,
            "classe": classe,
            "class_id": int(codigo_classe.value)
        }
    )

    atualizar_lista(selecionar_id=props_antigas["id"])
    status.value = f"<span style='color:green'>Classe '{classe}' salva.</span>"


def excluir_poligono(_):
    geometria = obter_geometria_selecionada()

    if geometria is None:
        status.value = "<span style='color:red'>Selecione um polígono.</span>"
        return

    draw.remove_geometry(geometria)
    atualizar_lista()
    status.value = "<span style='color:orange'>Polígono excluído.</span>"


# ---------- Eventos ----------
draw.on_geometry_create(ao_criar_poligono)
seletor.observe(ao_selecionar, names="value")
btn_salvar.on_click(salvar_classe)
btn_excluir.on_click(excluir_poligono)


# Painel sobre o mapa
m.add_widget(
    painel,
    position="topright",
    opened=True,
    show_close_button=True,
    widget_icon="tag"
)

m