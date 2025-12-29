# Gridfinity Generator para A1 Mini

Aplicação web paramétrica para geração de organizadores Gridfinity, desenvolvida especificamente para otimizar o fluxo de trabalho com impressoras 3D compactas como a Bambu Lab A1 Mini.

## 📋 Resumo do Projeto

Este projeto consiste numa ferramenta interativa desenvolvida em Python (Streamlit) e Build123d, capaz de gerar modelos 3D paramétricos do sistema modular Gridfinity. A aplicação foca-se em resolver a limitação de volume de impressão da A1 Mini (180mm³), implementando um algoritmo de "Smart Tiling" que divide automaticamente baseplates grandes em secções imprimíveis, mantendo a compatibilidade estrutural.

A ferramenta permite a exportação tanto em malha (STL) para impressão direta, quanto em corpos sólidos (STEP) para edição técnica em softwares CAD como SolidWorks.

## 🚀 Funcionalidades Principais

*   **Parametrização Total**: Geração baseada nas dimensões reais da gaveta (mm) ou unidades de grid.
*   **Smart Tiling (Divisão Inteligente)**: Algoritmo que segmenta baseplates excedentes a 4x4 unidades para caber na mesa da A1 Mini.
*   **Exportação CAD (STEP)**: Gera ficheiros `.step` (ISO 10303-21) contendo geometria B-Rep precisa para importação e edição em SolidWorks/Fusion 360.
*   **Exportação Impressão (STL)**: Gera malhas otimizadas prontas para fatiar.
*   **Geração de Bins**: Criação de caixas customizáveis com opções de etiquetas, divisórias e alturas variáveis.

## 🛠️ Tecnologias Utilizadas

*   **Linguagem**: Python 3.10+
*   **Frontend**: Streamlit
*   **Modelação Geétrica**: Build123d (Kernel OpenCascade)
*   **Processamento**: NumPy, Scipy

## 📦 Estrutura do Módulo

O núcleo da aplicação reside no pacote `gridfinity`, estruturado da seguinte forma:

```text
gridfinity/
├── baseplate.py    # Lógica de geração e divisão de baseplates
├── bins.py         # Lógica de modelação dos bins e divisórias
├── export_utils.py # Utilitários para exportação STL/STEP e ZIP
└── constants.py    # Definições padronizadas do sistema Gridfinity
```

## 🔧 Instalação e Execução

Para executar a aplicação localmente:

1.  **Configurar ambiente:**
    ```bash
    # Linux/Mac
    ./run.sh
    
    # Windows
    run.bat
    ```

    *Os scripts acima criam automaticamente o venv e instalam as dependências.*

2.  **Acesso:**
    Aceda a interface web através de: `http://localhost:8501`

## 📐 Especificações Técnicas Suportadas

*   **Unidade Base Gridfinity**: 42mm x 42mm
*   **Altura de Unidade**: 7mm (ex: 3u = 21mm + lip)
*   **Limite de Otimização A1 Mini**: 168mm x 168mm (4x4 unidades)

---
**Desenvolvido no âmbito de projeto académico (FEUP).**
