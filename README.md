# 📊 Dashboard Corporativo com Upload e IA

Sistema web para gestão, upload e análise de arquivos, com suporte a geração de **resumos automáticos por IA** (OpenAI ou local), controle de usuários, dashboard dinâmico e processamento sob demanda.

---

## ✨ **Funcionalidades Principais**

- **Cadastro, login e proteção de rotas** para usuários
- **Upload e download** de arquivos (.pdf, .docx, .xlsx, .txt, ...)
- **Exclusão** de arquivos (seguro, apenas pelo dono)
- **Geração de resumo automático por IA**
  - **OpenAI GPT** (usando sua própria chave, opcional)
  - **Resumo local** (Sumy/LSA) caso não queira gastar créditos OpenAI
- **Resumo IA sob demanda**
  - Botão para processar por arquivo individual
  - Processamento em lote de arquivos selecionados
- **Dashboard dinâmico**: estatísticas, atividades recentes, preview de resumo IA
- **Área de testes de IA**: envie arquivos para experimentar a IA sem salvar no banco

---

## 🏗️ **Tecnologias Usadas**

- **Python 3.10+**
- **Flask**
- **MySQL**
- **OpenAI API** (opcional, para resumos GPT)
- **Sumy + NLTK** (para resumo local)
- **PyPDF2, python-docx, openpyxl** (leitura de arquivos)
- **HTML5, CSS3 (moderno), Jinja2**

---

## 🚀 **Como rodar o projeto localmente**

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seuusuario/nome-do-repo.git
   cd nome-do-repo

2. **Crie um ambiente virtual**
    ```bash
    python -m venv venv
    source .\venv\Scripts\Activate # (ou venv\Scripts\activate no Windows)

3. **Instale as dependências**
    ```bash
    pip install -r requirements.txt

4. **Configure o arquivo .env**
    ```bash
        FLASK_ENV=development
        SECRET_KEY=sua_chave_secreta
        MYSQL_HOST=localhost
        MYSQL_USER=usuario
        MYSQL_PASSWORD=senha
        MYSQL_DATABASE=nome_db
        UPLOAD_FOLDER=uploads
        # Ative OpenAI se quiser:
        USE_OPENAI=true
        OPENAI_API_KEY=sua-chave-openai-aqui

5. **Baixe os recursos do NLTK necessários (só uma vez):**
    ```bash
    python -c "import nltk; nltk.download('punkt')"

6. **Crie o banco de dados e a tabela arquivo** 
    ```bash
        CREATE TABLE arquivo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome_arquivo VARCHAR(255),
        caminho VARCHAR(255),
        usuario_id INT,
        setor VARCHAR(100),
        resumo TEXT,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
    );

7. **Rode a aplicação**  
    ```bash
    flask run

---

## **⚙️ Principais Rotas** 

- **/ — Dashboard (requer login)**

- **/upload — Upload de arquivos**

- **/download/<arquivo_id> — Download de arquivos**

- **/delete/<arquivo_id> — Excluir arquivo**

- **/gerar_resumo/<arquivo_id> — Gerar/atualizar resumo IA de um arquivo**

- **/gerar_resumo_lote — Gerar resumo IA em lote (checkbox)**

- **/teste_ia — Laboratório de testes de IA**

---

## **💡 Como usar a IA** 

- **Por padrão, a IA local (Sumy/LSA) é usada.**

- **Para usar OpenAI GPT, ative no .env:**
    ```bash
    USE_OPENAI=true
    OPENAI_API_KEY=sua-chave-openai

- **Se sua chave OpenAI não tiver créditos, a IA local é usada como fallback.**

---

## **👨‍💻 Contribuição** 

- **Sinta-se livre para abrir issues, sugerir melhorias ou enviar PRs!**

- **Este projeto é um ótimo ponto de partida para sistemas corporativos com automação inteligente e dashboard moderno.**

---

## **🛡️ Avisos** 

- **Nunca compartilhe sua chave OpenAI publicamente.**

- **Adicione .env ao .gitignore.**

- **Não use o server Flask de desenvolvimento em produção.**

---

## **📚 Licença** 

- **MIT.**

- **Créditos: Daniel Ambrosim Colodete**