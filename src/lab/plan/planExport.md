## PLano de execução de 3 funções 

As funçõe deverão ser criadas na classe de Export em ``repository_ee``
Abaixo terá o exemplo de como deverá ser as 3 funções:

# --- ARQUIVO 1: Matriz de Confusão (Validação) ---
df_cm_val = pd.DataFrame(
    cm_val,
    index=[f"Real_{c}" for c in classes],
    columns=[f"Predito_{c}" for c in classes],
)
df_cm_val.to_csv("matriz_confusao_validacao.csv", index=True)

# --- ARQUIVO 2: Métricas por Classe (Produtor e Consumidor) ---
# Nota: producers_accuracy e consumers_accuracy retornam listas aninhadas do GEE (ex: [[0.9], [0.8]])
df_metricas_classe = pd.DataFrame({
    "Classe": classes,
    "Acuracia_Produtor": [
        item[0] if isinstance(item, list) else item for item in prod_acc
    ],
    "Acuracia_Consumidor": [
        item[0] if isinstance(item, list) else item for item in cons_acc
    ],
})
df_metricas_classe.to_csv("metricas_por_classe_validacao.csv", index=False)

# --- ARQUIVO 3: Resumo das Métricas Globais ---
df_resumo = pd.DataFrame([{
    "Acuracia_Treinamento": acc_treino,
    "Acuracia_Validacao": acc_val,
    "Kappa_Validacao": kappa_val,
}])
df_resumo.to_csv("resumo_metricas_rf.csv", index=False)

print("Arquivos CSV exportados com sucesso!")