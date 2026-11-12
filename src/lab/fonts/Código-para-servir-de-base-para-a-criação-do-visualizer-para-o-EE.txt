import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import os

class NaiveBayesVisualizer:
    """
    Visualizador para resultados do classificador Naive Bayes.
    Exibe gráficos 2D para Breast Cancer e Iris com métricas (acurácia e tempo).
    """
    
    def __init__(self, figsize=(10, 8), dpi=100, output_dir='./plots'):
        self.figsize = figsize
        self.dpi = dpi
        self.output_dir = output_dir
        
        # Criar diretório de saída se não existir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _adicionar_metricas(self, ax, accuracy, train_time, pred_time, dataset_name):
        """
        Adiciona informações de acurácia e tempo no canto inferior direito do gráfico.
        
        Args:
            ax: matplotlib axis object
            accuracy: taxa de acerto em percentual (ex: 95.67)
            train_time: tempo de treinamento em segundos
            pred_time: tempo de predição em segundos
            dataset_name: nome do dataset para contexto
        """
        tempo_total = train_time + pred_time
        
        texto = (
            f"METRICAS ({dataset_name})\n"
            f"────────────────────\n"
            f"Acurácia: {accuracy:.2f}%\n"
            f"Treino: {train_time:.4f}s\n"
            f"Predição: {pred_time:.4f}s\n"
            f"Total: {tempo_total:.4f}s"
        )
        
        # Adicionar texto com sombra no canto inferior direito
        ax.text(
            0.98, 0.02,  # posição: inferior direito (coordenadas normalizadas)
            texto,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(
                boxstyle='round,pad=0.8',
                facecolor='white',
                alpha=0.85,
                edgecolor='gray',
                linewidth=1.5
            ),
            family='monospace',
            weight='bold'
        )
    
    def plot_breast_cancer(self, X_test, y_test, y_pred, accuracy, train_time, pred_time):
        """
        Plota classificação Breast Cancer (M vs B) usando PCA para reduzir a 2D.
        
        Args:
            X_test: variáveis de teste (569, 30)
            y_test: rótulos verdadeiros (M ou B)
            y_pred: predições do modelo (M ou B)
            accuracy: taxa de acerto em percentual
            train_time: tempo de treinamento em segundos
            pred_time: tempo de predição em segundos
        """
        # Reduzir para 2D usando PCA
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_test)
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Cores: M = vermelho, B = azul
        cores = {'M': '#e74c3c', 'B': '#3498db'}
        marcadores_acerto = 'o'
        marcadores_erro = 'x'
        tamanho_acerto = 80
        tamanho_erro = 150
        
        # Plotar cada classe
        for classe in ['M', 'B']:
            mask_classe = y_test == classe
            indices_classe = np.where(mask_classe)[0]
            
            # Separar acertos e erros
            acertos = indices_classe[y_pred[indices_classe] == classe]
            erros = indices_classe[y_pred[indices_classe] != classe]
            
            # Plotar acertos (círculos)
            ax.scatter(
                X_pca[acertos, 0],
                X_pca[acertos, 1],
                c=cores[classe],
                marker=marcadores_acerto,
                s=tamanho_acerto,
                alpha=0.7,
                label=f"{classe} (Correto)",
                edgecolors='black',
                linewidth=0.5
            )
            
            # Plotar erros (X's)
            if len(erros) > 0:
                ax.scatter(
                    X_pca[erros, 0],
                    X_pca[erros, 1],
                    c=cores[classe],
                    marker=marcadores_erro,
                    s=tamanho_erro,
                    alpha=0.9,
                    label=f"{classe} (Erro)",
                    linewidth=1.5
                )
        
        ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variância)', fontsize=12, weight='bold')
        ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variância)', fontsize=12, weight='bold')
        ax.set_title('Classificação Naive Bayes - Breast Cancer\n(M = Maligno | B = Benigno)', 
                     fontsize=14, weight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Adicionar métricas no canto inferior direito
        self._adicionar_metricas(ax, accuracy, train_time, pred_time, "Breast Cancer")
        
        plt.tight_layout()
        
        # Salvar figura em vez de exibir
        output_path = os.path.join(self.output_dir, 'breast_cancer_classification.png')
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Gráfico salvo em: {output_path}")
        plt.close()
    
    def plot_iris(self, X_test, y_test, y_pred, accuracy, train_time, pred_time):
        """
        Plota classificação Iris (3 espécies) usando variáveis petal_length vs petal_width.
        
        Args:
            X_test: variáveis de teste (150, 4) - [sepal_length, sepal_width, petal_length, petal_width]
            y_test: rótulos verdadeiros (setosa, versicolor, virginica)
            y_pred: predições do modelo
            accuracy: taxa de acerto em percentual
            train_time: tempo de treinamento em segundos
            pred_time: tempo de predição em segundos
        """
        # variáveis mais discriminativas: petal_length (índice 2) vs petal_width (índice 3)
        X_plot = X_test[:, [2, 3]]
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Cores e nomes das espécies
        classes_info = {
            'setosa': {'cor': '#e74c3c', 'nome': 'Setosa'},
            'versicolor': {'cor': '#3498db', 'nome': 'Versicolor'},
            'virginica': {'cor': '#2ecc71', 'nome': 'Virginica'}
        }
        
        marcadores_acerto = 'o'
        marcadores_erro = 'x'
        tamanho_acerto = 100
        tamanho_erro = 180
        
        # Plotar cada espécie
        for classe in ['setosa', 'versicolor', 'virginica']:
            mask_classe = y_test == classe
            indices_classe = np.where(mask_classe)[0]
            
            # Separar acertos e erros
            acertos = indices_classe[y_pred[indices_classe] == classe]
            erros = indices_classe[y_pred[indices_classe] != classe]
            
            cor = classes_info[classe]['cor']
            nome = classes_info[classe]['nome']
            
            # Plotar acertos (círculos)
            ax.scatter(
                X_plot[acertos, 0],
                X_plot[acertos, 1],
                c=cor,
                marker=marcadores_acerto,
                s=tamanho_acerto,
                alpha=0.7,
                label=f"{nome} (Correto)",
                edgecolors='black',
                linewidth=0.5
            )
            
            # Plotar erros (X's)
            if len(erros) > 0:
                ax.scatter(
                    X_plot[erros, 0],
                    X_plot[erros, 1],
                    c=cor,
                    marker=marcadores_erro,
                    s=tamanho_erro,
                    alpha=0.9,
                    label=f"{nome} (Erro)",
                    linewidth=1.5
                )
        
        ax.set_xlabel('Comprimento da Pétala (cm)', fontsize=12, weight='bold')
        ax.set_ylabel('Largura da Pétala (cm)', fontsize=12, weight='bold')
        ax.set_title('Classificação Naive Bayes - Iris\n(3 Espécies de Flores)', 
                     fontsize=14, weight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Adicionar métricas no canto inferior direito
        self._adicionar_metricas(ax, accuracy, train_time, pred_time, "Iris")
        
        plt.tight_layout()
        
        # Salvar figura em vez de exibir
        output_path = os.path.join(self.output_dir, 'iris_classification.png')
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Gráfico salvo em: {output_path}")
        plt.close()
