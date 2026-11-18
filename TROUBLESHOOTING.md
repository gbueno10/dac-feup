# 🔧 Solução de Problemas

## ⚠️ Erro: "Não foi possível verificar se o OpenSCAD é seguro"

Se você receber este erro no macOS ao tentar gerar um STL:

### Solução:

1. **Abra o Terminal** e execute:
```bash
xattr -d com.apple.quarantine /Applications/OpenSCAD-2021.01.app
```

2. **Ou vá em Preferências do Sistema:**
   - Vá em: **Configurações do Sistema** → **Privacidade e Segurança**
   - Role até o final e clique em **Abrir Mesmo Assim** ao lado da mensagem sobre o OpenSCAD
   - Digite sua senha quando solicitado

### Por que isso acontece?

O macOS bloqueia aplicativos baixados da internet que não são assinados pela Apple. O comando `xattr` remove essa quarentena.

---

## 🧪 Teste Rápido

Para verificar se o OpenSCAD está funcionando:

```bash
openscad --version
```

Deve retornar: `OpenSCAD version 2021.01`

---

## 📦 Gerando seu Primeiro STL

1. Abra a aplicação (se ainda não estiver rodando):
```bash
source venv/bin/activate
streamlit run app.py
```

2. Acesse: http://localhost:8501

3. Configure as dimensões e clique em **🚀 Gerar STL**

4. Aguarde alguns segundos e faça o download!

---

## 🆘 Outros Problemas

### O Streamlit não inicia
```bash
# Certifique-se de que o venv está ativo
source venv/bin/activate

# Reinstale se necessário
pip install streamlit
```

### Erro ao gerar STL
- Verifique se os arquivos `.scad` estão na pasta (rode `./download_scad_files.sh`)
- Verifique se o OpenSCAD está instalado: `brew list openscad`
- Verifique o caminho no `app.py` (variável `CAMINHO_OPENSCAD`)
