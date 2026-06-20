# NullBank - Sistema de Controle Bancário

Projeto final da disciplina de Banco de Dados, período 2026.1, do curso de Engenharia da Computação do Campus de Sobral. 

Este sistema gerencia as operações de uma instituição bancária (NullBank), suportando o cadastro de agências, funcionários, clientes e o processamento de transações financeiras.

**Professor:** Fernando Rodrigues de Almeida Júnior
**Equipe**
- Antônio Kildere Sousa Menezes – Matrícula: 567258
- José Arthur Gomes Azevedo – Matrícula: 567419
- Daniel Neco Silva – Matrícula: 568270

---

## 🛠 Tecnologias Utilizadas

*   **Frontend:** Python (Streamlit)
*   **Banco de Dados:** MySQL (versão 5.7+)
*   **Ferramenta CASE:** MySQL Workbench
*   **Infraestrutura:** Docker e Docker Compose

---

## ⚙️ Funcionalidades e Regras de Negócio

O NullBank foi modelado para suportar o ecossistema bancário completo:

*   **Agências e Funcionários:** Controle de agências (com cálculo automático do montante total de salários) e gestão de funcionários classificados por cargos (gerente, atendente ou caixa). Os funcionários podem registrar até 5 dependentes para fins de plano de saúde.
*   **Clientes e Contas:** Um cliente pode possuir no máximo uma conta por agência. O sistema suporta contas-correntes, contas poupança (com taxa de juros) e contas especiais (com limite de crédito). Contas conjuntas são suportadas para até 2 titulares.
*   **Transações:** Registro imutável de saques, depósitos, pagamentos, estornos, transferências e PIX. O saldo da conta reflete automaticamente o conjunto de transações, impedindo saldos negativados (exceto dentro do limite de crédito em contas especiais).

### 🔐 Controle de Acesso
O sistema implementa três níveis hierárquicos de acesso:
1.  **DBA (Administrador):** Acesso total ao sistema e banco de dados via credenciais `Admin` / `Root`.
2.  **Funcionários (Login via Matrícula):**
    *   *Gerentes:* Cadastram contas, clientes e funcionários, mas não realizam movimentações financeiras diretas.
    *   *Caixas:* Acesso irrestrito às transações financeiras das contas da sua respectiva agência.
    *   *Atendentes:* Acesso exclusivo de leitura para consultas de contas e saldos na sua agência.
3.  **Clientes (Login via CPF):** Acesso às suas próprias contas para visualização e operações, com tela de seleção caso possua múltiplas contas.

---

## 📂 Estrutura do Repositório

*   `app.py`: Ponto de entrada da aplicação frontend em Streamlit.
*   `bd.mwb`: Arquivo de modelagem conceitual/física desenvolvida no MySQL Workbench.
*   `bd.sql`: Scripts contendo a DDL (criação das tabelas) e DML (povoamento inicial do banco). O banco é nomeado como `Equipe567258`.
*   `Consultas.sql`: Arquivo contendo todas as consultas solicitadas nas especificações, além da criação de visões (views), gatilhos (triggers) para atualização de saldos e a transação segura para transferência entre contas.
*   `requirements.txt`: Dependências Python necessárias para rodar o projeto.
*   `docker-compose.yml` e `Dockerfile`: Arquivos para orquestração do ambiente de desenvolvimento.

---

## 🚀 Como Executar o Projeto Localmente

Embora o sistema operacional sugerido seja o Windows 10+, a aplicação foi containerizada para rodar de forma isolada em qualquer ambiente de desenvolvimento usando o Docker.

### Passo 1: Iniciar os Containers (Banco + Frontend)
Na raiz do projeto, suba a infraestrutura utilizando o Docker Compose. Isso iniciará o banco de dados MySQL e a aplicação Streamlit conectada a ele.
```bash
docker compose up -d --build
```

### Passo 2: Acessar a Aplicação
Após os containers iniciarem com sucesso, abra o seu navegador e acesse a porta exposta pelo Streamlit:

http://localhost:8501
(Nota: Caso deseje rodar a aplicação nativamente sem o Docker, certifique-se de ter o Python 3.11+ instalado, crie um ambiente virtual, instale as dependências com pip install -r requirements.txt e execute streamlit run app.py).