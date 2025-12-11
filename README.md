# Gridfinity Generator Web App

Ferramenta web para gerar arquivos Gridfinity baseados nas medidas reais de uma gaveta, otimizado para Bambu Lab A1 Mini.

## Funcionalidades

- **Smart Tiling**: Divide automaticamente baseplates grandes em peças que cabem na A1 Mini (max 4x4 unidades)
- **Geração de Bins**: Crie caixas Gridfinity personalizadas
- **Validação Automática**: Alertas de incompatibilidade para peças muito grandes
- **Download Unificado**: Arquivo ZIP com todas as peças

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

## Hardware Alvo

- **Bambu Lab A1 Mini**: Volume 180x180x180mm
- Limite seguro: 4x4 unidades (168mm)

## Especificações Gridfinity

- Unidade base: 42mm x 42mm
- Altura da unidade: 7mm
