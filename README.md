# 📦 Fábrica Gridfinity Local

Interface web para gerar caixas Gridfinity usando OpenSCAD e Python/Streamlit.

## 🎯 Sobre o Projeto

Este projeto cria uma interface gráfica moderna para o sistema Gridfinity, permitindo gerar caixas organizadoras personalizadas para impressão 3D sem precisar editar código OpenSCAD manualmente.

## 📋 Pré-requisitos

### 1. OpenSCAD Instalado
Você precisa ter o OpenSCAD instalado no seu computador:

- **macOS**: Baixe em https://openscad.org/downloads.html
- **Windows**: Baixe em https://openscad.org/downloads.html
- **Linux**: `sudo apt-get install openscad` (Ubuntu/Debian)

### 2. Python 3.8+
Verifique se você tem Python instalado:
```bash
python --version
```

### 3. Arquivos SCAD do Gridfinity
Você precisa baixar os arquivos `.scad` do repositório Gridfinity e colocá-los nesta pasta:

- `gridfinity_basic_cup.scad` (arquivo principal)
- `gridfinity_modules.scad` (dependência)
- `gridfinity_cup_modules.scad` (dependência)

**Link do repositório**: https://github.com/kennetek/gridfinity-rebuilt-openscad

## 🚀 Como Usar

### 1. Instalar Dependências Python
```bash
pip install -r requirements.txt
```

### 2. Configurar Caminho do OpenSCAD
Se o comando `openscad` não funcionar diretamente no terminal, você precisa editar o arquivo `app.py` e configurar o caminho:

**No macOS:**
```python
CAMINHO_OPENSCAD = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
```

**No Windows:**
```python
CAMINHO_OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"
```

### 3. Baixar os Arquivos SCAD
Certifique-se de que os arquivos `.scad` estão na mesma pasta do `app.py`:
```
trabalho-dac/
├── app.py
├── requirements.txt
├── README.md
├── gridfinity_basic_cup.scad      ← IMPORTANTE
├── gridfinity_modules.scad        ← IMPORTANTE
└── gridfinity_cup_modules.scad    ← IMPORTANTE
```

### 4. Rodar a Aplicação
```bash
streamlit run app.py
```

O navegador vai abrir automaticamente com a interface!

## 🎨 Funcionalidades

- **Dimensões Personalizáveis**: Largura, profundidade e altura
- **Divisórias**: Compartimentos internos configuráveis
- **Aba de Etiqueta**: Opcional para identificação
- **Arredondamento Interno**: Para facilitar a retirada de objetos
- **Furos para Ímãs**: Sistema de fixação magnética

## 🐛 Solução de Problemas

### Erro: "O executável do OpenSCAD não foi encontrado"
1. Verifique se o OpenSCAD está instalado
2. No macOS, abra o terminal e teste: `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD --version`
3. Edite o caminho no arquivo `app.py` na linha do `CAMINHO_OPENSCAD`

### Erro ao gerar STL
1. Verifique se os arquivos `.scad` estão na pasta correta
2. Verifique os logs de erro na interface (expanda "Ver detalhes do erro")

## 📚 Estrutura do Código

```python
app.py              # Aplicação principal Streamlit
├── Configuração    # Caminho do OpenSCAD
├── Frontend        # Interface com Streamlit
└── Backend         # Wrapper para executar OpenSCAD via subprocess
```

## 🎓 Para o Professor

Este projeto demonstra:
- **Automação**: Wrapper Python para ferramenta de linha de comando
- **Interface Gráfica**: GUI moderna com Streamlit
- **Integração de Sistemas**: Python + OpenSCAD
- **Engenharia Smart**: Reutilização de código existente (.scad) com nova interface

## 📝 Licença

Este projeto é para fins educacionais. Os arquivos Gridfinity originais seguem suas próprias licenças.
